import base64
import os
import torch
import torchaudio
import numpy as np
import onnxruntime
import re
import random
import math
import pickle
from typing import Dict, Union, List
from pypinyin import lazy_pinyin, Style
from dotenv import load_dotenv, find_dotenv
import runpod

# Завантаження змінних середовища
load_dotenv(find_dotenv('.env_prod'))

# Константи
HOP_LENGTH = 256
SAMPLE_RATE = 24000
RANDOM_SEED = random.randint(0, 1000000)

# Шляхи до моделей та файлів
ONNX_MODEL_PATH = os.getenv("F5_Preprocess")
VOCAB_FILE = os.getenv("vocab_file")

if not ONNX_MODEL_PATH or not VOCAB_FILE:
    raise ValueError("F5_Preprocess or vocab_file not found in environment variables")

# Завантаження словника
with open(VOCAB_FILE, "r", encoding="utf-8") as f:
    VOCAB_CHAR_MAP = {char[:-1]: i for i, char in enumerate(f)}

# Налаштування ONNX сесії
SESSION_OPTS = onnxruntime.SessionOptions()
SESSION_OPTS.log_severity_level = 3  # error level
SESSION_OPTS.inter_op_num_threads = 0  # Run different nodes with num_threads. Set 0 for auto.
SESSION_OPTS.intra_op_num_threads = 0  # Under the node, execute the operators with num_threads. Set 0 for auto.
SESSION_OPTS.enable_cpu_mem_arena = True  # True for execute speed
SESSION_OPTS.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
SESSION_OPTS.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
SESSION_OPTS.enable_mem_pattern = True
SESSION_OPTS.enable_mem_reuse = True
onnxruntime.set_seed(RANDOM_SEED)

def convert_char_to_pinyin(text_list: Union[List[str], List[List[str]]], polyphone: bool = True) -> List[List[str]]:
    """Конвертує текст в піньїнь"""
    final_text_list = []

    def replace_quotes(text: str) -> str:
        return text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'").replace(';', ',')

    def is_japanese(c: str) -> bool:
        return (
                '\u3040' <= c <= '\u309F' or  # Hiragana
                '\u30A0' <= c <= '\u30FF' or  # Katakana
                '\uFF66' <= c <= '\uFF9F'  # Half-width Katakana
        )

    for text in text_list:
        char_list = []
        text = replace_quotes(text)
        
        for seg in text:
            seg_byte_len = len(seg.encode('utf-8'))
            if seg_byte_len == len(seg):  # ASCII text
                if char_list and seg_byte_len > 1 and char_list[-1] not in " :'\"":
                    char_list.append(" ")
                char_list.extend(seg)
            elif polyphone and seg_byte_len == 3 * len(seg):  # Pure Chinese text
                seg_pinyin = lazy_pinyin(seg, style=Style.TONE3, tone_sandhi=True)
                for p in seg_pinyin:
                    if p not in "。，、；：？！《》【】—…":
                        if not char_list or not is_japanese(char_list[-1]):
                            char_list.append(" ")
                    char_list.append(p)
            else:  # Mixed text or other languages
                for c in seg:
                    if ord(c) < 256:  # ASCII character
                        char_list.append(c)
                    elif is_japanese(c):  # Japanese character
                        char_list.append(c)
                    else:
                        if c not in "。，、；：？！《》【】—…":
                            pinyin = lazy_pinyin(c, style=Style.TONE3, tone_sandhi=True)
                            char_list.extend(pinyin)
                        else:
                            char_list.append(c)
        final_text_list.append(char_list)
    return final_text_list

def list_str_to_idx(
    text: Union[List[str], List[List[str]]],
    vocab_char_map: Dict[str, int],
    padding_value: int = -1
) -> torch.Tensor:
    """Конвертує список строк в тензор індексів"""
    get_idx = vocab_char_map.get
    list_idx_tensors = [torch.tensor([get_idx(c, 0) for c in t], dtype=torch.int32) for t in text]
    text = torch.nn.utils.rnn.pad_sequence(list_idx_tensors, padding_value=padding_value, batch_first=True)
    return text

def preprocess_text_and_audio(
    reference_audio: str,
    ref_text: str,
    lang: str = 'zh'
) -> bytes:
    """
    Виконує препроцесинг референсного тексту та аудіо.
    
    Args:
        reference_audio: Шлях до референсного аудіо файлу
        ref_text: Референсний текст
        lang: Мова тексту ('zh' або 'en')
        
    Returns:
        bytes: Серіалізовані результати препроцесингу у форматі pickle
    """
    # Завантаження та обробка аудіо

    print(reference_audio, ref_text, lang)

    audio, sr = torchaudio.load(reference_audio)
    if sr != SAMPLE_RATE:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=SAMPLE_RATE)
        audio = resampler(audio)
    audio = audio.unsqueeze(0).numpy()
    
    # Створення ONNX сесії
    ort_session = onnxruntime.InferenceSession(
        ONNX_MODEL_PATH,
        sess_options=SESSION_OPTS,
        providers=['CUDAExecutionProvider']
    )

    # Отримання імен входів/виходів моделі
    in_names = [input.name for input in ort_session.get_inputs()]
    out_names = [output.name for output in ort_session.get_outputs()]
    model_type = ort_session._inputs_meta[0].type

    # Конвертація аудіо у float16 якщо потрібно
    if "float16" in model_type:
        audio = audio.astype(np.float16)

    # Розрахунок довжини тексту
    if lang == 'zh':
        zh_pause_punc = r"。，、；：？！"
        ref_text_len = len(ref_text.encode('utf-8')) + 3 * len(re.findall(zh_pause_punc, ref_text))
    else:
        ref_text_len = len(ref_text.encode('utf-8'))

    # Розрахунок максимальної тривалості
    ref_audio_len = audio.shape[-1] // HOP_LENGTH + 1
    max_duration = np.array(ref_audio_len, dtype=np.int64)

    # Конвертація тексту
    text_ids = list_str_to_idx(
        convert_char_to_pinyin([ref_text]), 
        VOCAB_CHAR_MAP
    ).numpy()

    # Виконання інференсу ONNX моделі
    outputs = ort_session.run(
        out_names,
        {
            in_names[0]: audio,
            in_names[1]: text_ids,
            in_names[2]: max_duration
        }
    )

    # Створення time_expand тензора
    t = torch.linspace(0, 1, 32 + 1, dtype=torch.float32)
    time_step = t + (-1.0) * (torch.cos(torch.pi * 0.5 * t) - 1 + t)
    delta_t = torch.diff(time_step)
    
    time_expand = torch.zeros((1, 32, 256), dtype=torch.float32)
    half_dim = 256 // 2
    emb_factor = math.log(10000) / (half_dim - 1)
    emb_factor = 1000.0 * torch.exp(torch.arange(half_dim, dtype=torch.float32) * -emb_factor)
    
    for i in range(32):
        emb = time_step[i] * emb_factor
        time_expand[:, i, :] = torch.cat((emb.sin(), emb.cos()), dim=-1)

    # Формування результату
    result = (
        outputs[0],  # noise
        outputs[3],  # cat_mel_text
        outputs[4],  # cat_mel_text_drop
        time_expand.numpy(),
        outputs[1],  # rope_cos
        outputs[2],  # rope_sin
        delta_t.numpy(),
        outputs[6]   # ref_signal_len
    )

    # Серіалізація результату
    return pickle.dumps(result)

def handler(event):
    print(event)  
    input = event["input"]
    audio = base64.b64decode(input["reference_audio"])
    return preprocess_text_and_audio(audio, input["ref_text"], input["lang"])


runpod.serverless.start({"handler": handler})