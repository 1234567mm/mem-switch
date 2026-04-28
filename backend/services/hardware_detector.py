import psutil
from dataclasses import dataclass


@dataclass
class HardwareInfo:
    cpu_cores: int
    total_memory_gb: float
    gpu_available: bool
    gpu_memory_gb: float
    gpu_name: str


MODEL_RECOMMENDATIONS = {
    "low": {
        "llm": ["qwen2.5:0.5b", "tinyllama"],
        "embedding": "nomic-embed-text",
        "label": "轻量模式 (<4GB)",
    },
    "medium": {
        "llm": ["qwen2.5:1.5b", "mistral:7b-q4_K_M"],
        "embedding": "nomic-embed-text",
        "label": "中等模式 (4-8GB)",
    },
    "high": {
        "llm": ["qwen2.5:7b", "llama3.1:8b"],
        "embedding": "nomic-embed-text",
        "label": "高性能模式 (8-16GB)",
    },
    "ultra": {
        "llm": ["qwen2.5:14b", "llama3.1:70b-q4_K_M"],
        "embedding": "nomic-embed-text",
        "label": "超强模式 (16GB+/GPU)",
    },
}


def detect_hardware() -> HardwareInfo:
    cpu_cores = psutil.cpu_count(logical=True)
    total_memory_gb = psutil.virtual_memory().total / (1024 ** 3)
    gpu_available = False
    gpu_memory_gb = 0.0
    gpu_name = ""

    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_available = True
            gpu_memory_gb = gpus[0].memoryTotal / 1024
            gpu_name = gpus[0].name
    except (ImportError, Exception):
        pass

    return HardwareInfo(
        cpu_cores=cpu_cores,
        total_memory_gb=round(total_memory_gb, 1),
        gpu_available=gpu_available,
        gpu_memory_gb=round(gpu_memory_gb, 1),
        gpu_name=gpu_name,
    )


def recommend_models(hw: HardwareInfo) -> dict:
    ram = hw.total_memory_gb

    if ram < 4:
        tier = "low"
    elif ram < 8:
        tier = "medium"
    elif ram < 16:
        tier = "high"
    else:
        tier = "ultra"

    if hw.gpu_available and hw.gpu_memory_gb >= 8:
        tier = "ultra"

    rec = MODEL_RECOMMENDATIONS[tier]
    return {
        "tier": tier,
        "recommended_llm": rec["llm"],
        "recommended_embedding": rec["embedding"],
        "label": rec["label"],
        "hardware": hw,
    }
