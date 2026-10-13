# 压缩试验 CPU 环境配方 v1

适用范围：Windows x64、Python 3.11.15、torch 2.5.1+cpu、NumPy 2.1.2。这是压缩试验的最小环境，不替代原项目完整模型环境。原 `.venv` 未修改；验证环境放在 gitignored 的 `data/engineering-cpu-validation-20261013-v1/.venv`。

## 配方

创建新的目录；不要覆盖已有环境。以下命令在仓库根目录执行，把 Python 路径换成已核实的 3.11.15 解释器。

```powershell
D:/env/python.exe -m venv data/my-new-cpu-env/.venv
data/my-new-cpu-env/.venv/Scripts/python.exe -m pip install --no-deps -r requirements/torch-cpu.txt
data/my-new-cpu-env/.venv/Scripts/python.exe -m pip install -r requirements/compression-cpu.txt
```

PyTorch 官方的 [2.5.1 历史版本安装页](https://pytorch.org/get-started/previous-versions/)提供 Linux/Windows CPU wheel 索引。这里进一步明确 `+cpu`，避免误装 CUDA 轮。两个安装步骤分开，避免 `--index-url` 使全部项目依赖都只从 Torch CPU 索引解析。不要把 `torch-cu121.txt` 当作本批 CPU 配方。

若索引解析耗时，可使用经过本次 PyPI JSON API 查询、文件哈希绑定的 Windows CPython 3.11 直接 wheel 配方 `requirements/compression-cpu-win311-wheels.txt`。Torch CPU wheel 的直接文件 URL 为：

`https://download.pytorch.org/whl/cpu/torch-2.5.1%2Bcpu-cp311-cp311-win_amd64.whl`

```powershell
data/my-new-cpu-env/.venv/Scripts/python.exe -m pip install --no-deps --retries 1 --timeout 20 "https://download.pytorch.org/whl/cpu/torch-2.5.1%2Bcpu-cp311-cp311-win_amd64.whl"
data/my-new-cpu-env/.venv/Scripts/python.exe -m pip install --no-index --no-deps --require-hashes -r requirements/compression-cpu-win311-wheels.txt
data/my-new-cpu-env/.venv/Scripts/python.exe -m pip check
```

依赖版本逐项来自已运行的原实验环境，包含 numpy/filelock/typing_extensions/networkx/Jinja2/fsspec/sympy/mpmath/MarkupSafe。直接 wheel 配方是 Windows CPython 3.11 专用，不能冒充 Linux/macOS 锁文件。下载标准软件包不涉及 CDD 数据许可。

## 验收

```powershell
data/my-new-cpu-env/.venv/Scripts/python.exe -B -c "import sys,torch,numpy; print(sys.version); print(torch.__version__,numpy.__version__)"
data/my-new-cpu-env/.venv/Scripts/python.exe -B research_work/project_management_2026_10_10/compression_pilot_2026_10_13/run_pilot_v1.py --help
data/my-new-cpu-env/.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_fixed_ohlc_preprocessing.py -v
data/my-new-cpu-env/.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_compression_replay.py -v
```

验收只做导入、合成与门控检查，不读取真实角色数组、不训练、不评分。预期 Python 3.11.15 / torch 2.5.1+cpu / NumPy 2.1.2；本次实际安装与测试结果以工程实施目录的 `VALIDATION_RECEIPT_V1.json` 为准，配方本身不代表安装成功。

同操作系统和 CPU 架构只是逐位复现的必要候选条件，不足以保证所有数值路径一致。编译发行版、BLAS/线程和硬件差异也可能改变训练轨迹；真正重签复跑后必须对照历史张量哈希，失败不得放宽为成功。跨平台指标容差仍是待事先定义的研究判断。
