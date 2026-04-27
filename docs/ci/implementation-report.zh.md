# CV32E20-DV CI 实施报告

生成日期：2026-04-27

## 本次实际完成的内容

已完整克隆 upstream `openhwgroup/cv32e20-dv` 到本地：

```text
/Users/alexchen/1_workspace/4_openhw/2_cva6_ci/1_tier_v1/cv32e20-dv
```

克隆状态：

- 非 shallow clone。
- 当前基线：`main` 分支 `f54c88194b542efcb073bfcd6ad29c845ec307c7`。
- 工作分支：`codex/cv32e20-ci`。

## 已新增的 CI 文件

### cv32e20-dv 正式 workflow

```text
.github/workflows/cv32e20-dv-ci.yml
```

包含：

- `Core hello-world / verilator`
  - GitHub-hosted Ubuntu runner。
  - 安装/缓存 Verilator v5.046。
  - 安装/检查 RISC-V GCC toolchain。
  - 执行 `scripts/run-core-hello.sh`，即进入 `sim/core` 后运行 `make sanity`。

- `UVM hello-world / vsim`
  - self-hosted runner label: `[self-hosted, linux, questa]`。
  - 执行 `scripts/run-uvm-hello.sh vsim`。

- `UVM hello-world / dsim`
  - self-hosted runner label: `[self-hosted, linux, dsim]`。
  - 执行 `scripts/run-uvm-hello.sh dsim`。

### 工具 setup action

```text
.github/actions/setup-cv32e20-tools/action.yml
```

作用：

- 缓存和安装 Verilator v5.046。
- 安装或发现 `riscv64-unknown-elf-*` toolchain。
- 安装或发现 Sail RISC-V。
- 安装 `uv`。
- 检查 UDB 是否存在。
- 设置 `CV_SW_TOOLCHAIN`、`CV_SW_PREFIX`、`CV_SW_MARCH` 和 PATH。

### 运行脚本

```text
scripts/install-verilator.sh
scripts/install-riscv-toolchain.sh
scripts/install-sail.sh
scripts/install-uv.sh
scripts/check-udb.sh
scripts/run-core-hello.sh
scripts/run-uvm-hello.sh
scripts/run-act-certify.sh
```

这些脚本把 workflow 中的命令收敛到可本地复用的入口，避免 GitHub Actions YAML 里堆太多逻辑。

### cve2 workflow 模板

```text
cve2-ci-template/cve2-act-ci.yml
cve2-ci-template/README.md
```

作用：

- 提供应复制到 `cve2/.github/workflows/` 的 ACT4 CI。
- 该 workflow 对任意 PR 触发。
- clone `cv32e20-dv`，并用当前 cve2 PR head 覆盖 `CV_CORE_REPO/CV_CORE_BRANCH/CV_CORE_HASH`。
- 在 `cv32e20-dv/sim/core` 运行 `make gen-certify`。

### Dashboard

```text
.github/workflows/cv32e20-dashboard.yml
dashboard/collect_data.py
dashboard/generate_dashboard.py
dashboard/parser.py
dashboard/templates/index.html
```

作用：

- 在 CI workflow 完成后采集 GitHub Actions run/job 数据。
- 生成静态 HTML dashboard。
- 发布到 GitHub Pages。
- 用 `gh-pages-cv32e20-dashboard-data` 分支保存历史数据。

## 为什么这样设计

### 为什么 core hello-world 用 Verilator

Mike 明确提到 core testbench 已经可以用 Verilator v5.046 跑，并且支持 ACT4。这个路径完全开源，适合作为 PR 的快速 gating check。

### 为什么 UVM hello-world 放 self-hosted runner

Questa 和 DSim 是商业/托管工具，GitHub-hosted runner 不可能直接提供 license 和安装环境。因此 workflow 只声明 runner label，实际 toolchain/license 由 self-hosted runner 管理。

### 为什么 cve2 workflow 作为模板而不是直接放进 cv32e20-dv workflows

Mike 的规则是“任何到 cve2 的 PR”。GitHub Actions 的 PR trigger 必须在 `cve2` 仓库中生效。把它放进 `cv32e20-dv` 仓库不会监听 `cve2` PR，也会导致错误的 repository context。因此本仓库交付模板，并在报告中说明复制目标。

### 为什么保留 dashboard

你的 CVA6 Phase 1 已经证明 dashboard 对领导沟通很有价值。这里的 dashboard 先做最小版本，只显示 workflow/job 状态、分支、commit、耗时和历史 run。后续 coverage regression 稳定后，可以扩展覆盖率趋势和 UCDB/DSim report 链接。

## 验证结果

已完成本地静态检查：

- shell 脚本：`bash -n scripts/*.sh`
- Python 脚本：`python3 -m py_compile dashboard/*.py`
- YAML 解析：workflow 和 composite action 均可被 Ruby YAML parser 读取
- dashboard：使用 sample JSON 数据可生成 HTML

未在本地实际运行完整 simulation，原因：

- 本机当前未确认 Verilator v5.046、Sail、RISC-V toolchain、Questa、DSim、license 环境是否齐备。
- 完整 ACT4 和 UVM regression 更适合在目标 GitHub runner 上验证。

## 下一步

1. 推送 `codex/cv32e20-ci` 到你的私有 repo。
2. 在私有 repo 的 Actions 中先手动运行 `cv32e20-dv-ci`。
3. 如果 Verilator job 通过，再接入 Questa/DSim self-hosted runners。
4. 将 `cve2-ci-template/cve2-act-ci.yml` 和共享 scripts/action 复制到 `cve2` 私有镜像或 upstream 分支中验证。
5. 确认 runner labels、Sail tarball URL、UDB 需求后，把相关变量写入 GitHub repository variables/secrets。
