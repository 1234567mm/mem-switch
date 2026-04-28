from services.hardware_detector import HardwareInfo, recommend_models


def test_recommend_low_ram():
    hw = HardwareInfo(cpu_cores=2, total_memory_gb=2.0, gpu_available=False, gpu_memory_gb=0, gpu_name="")
    rec = recommend_models(hw)
    assert rec["tier"] == "low"
    assert rec["recommended_embedding"] == "nomic-embed-text"


def test_recommend_medium_ram():
    hw = HardwareInfo(cpu_cores=4, total_memory_gb=6.0, gpu_available=False, gpu_memory_gb=0, gpu_name="")
    rec = recommend_models(hw)
    assert rec["tier"] == "medium"


def test_recommend_high_ram():
    hw = HardwareInfo(cpu_cores=8, total_memory_gb=12.0, gpu_available=False, gpu_memory_gb=0, gpu_name="")
    rec = recommend_models(hw)
    assert rec["tier"] == "high"


def test_recommend_ultra_ram():
    hw = HardwareInfo(cpu_cores=16, total_memory_gb=32.0, gpu_available=True, gpu_memory_gb=12.0, gpu_name="RTX 4080")
    rec = recommend_models(hw)
    assert rec["tier"] == "ultra"


def test_gpu_upgrades_tier():
    hw = HardwareInfo(cpu_cores=4, total_memory_gb=6.0, gpu_available=True, gpu_memory_gb=10.0, gpu_name="RTX 3080")
    rec = recommend_models(hw)
    assert rec["tier"] == "ultra"
