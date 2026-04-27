# Mike 需求分析报告

生成日期：2026-04-27

## 背景

Mike 的消息说明，`cv32e20-dv` 在 PR #32 之后已经具备三类可工作的验证能力：

1. UVM testbench 可以在 Questa 2023.3_2 和 DSim 2026 上运行。
2. core testbench 可以在 Verilator v5.046 上运行。
3. core testbench 已支持 RISC-V Architectural Certification Tests v4.0，也就是 ACT4，并且当前全部通过。

这意味着项目已经从“功能 bring-up”进入“CI 回归和覆盖率回归建设”的阶段。Mike 想要的不是单个脚本，而是一套稳定的 GitHub Actions 入口、runner/tool 约束、触发规则和后续 dashboard/coverage 可扩展基础。

## Mike 的明确需求

### 1. 仓库流程清理

Mike 提到 open PR 中只有两个，且都是 `Do Not Merge`，其中 #26 需要周一讨论。他还建议把 `cv32e20-dv` 的 `dev` 分支同步到 `main`，之后恢复惯例：普通 PR target 到 `dev`，必要时 target 到 feature branch。

目的：

- 避免 CI 在不一致的 `main/dev` 上验证出不同结论。
- 让 CI required checks 有稳定的目标分支。
- 让后续 dashboard 的趋势数据不会混入旧分支状态。

本次实现不直接改 upstream 分支策略，但报告中把它列为启用 CI 前置条件。

### 2. cve2 仓库 CI 规则

Mike 建议：任何到 `cve2` 任意分支的 PR，都应该在 GitHub runner 上使用全开源代码和工具运行 ACT4，也就是 `gen-certify`。

目的：

- `cve2` 是 RTL 源头，RTL 变动必须快速证明没有破坏 RISC-V 架构认证测试。
- 使用 GitHub-hosted runner 和开源工具，可以避免商业 simulator license 变成 PR gating 的瓶颈。

实现方式：

- workflow 放在 `cve2/.github/workflows/cve2-act-ci.yml`。
- workflow checkout `cv32e20-dv`，再把当前 `cve2` PR head 作为 `CV_CORE_REPO/CV_CORE_BRANCH/CV_CORE_HASH` 传给 `cv32e20-dv/sim/ExternalRepos.mk` 机制。
- 在 `cv32e20-dv/sim/core` 执行 `make gen-certify`。
- 上传 `sim/core/simulation_results/` 作为 artifact，保留 ACT4 summary。

### 3. cv32e20-dv 仓库 CI 规则

Mike 建议：任何到 `cv32e20-dv/main` 的 PR，都应该在 UVM testbench 和 core testbench 上运行 `hello-world`。

目的：

- `cv32e20-dv` 自己的变动主要影响 testbench、BSP、脚本、test yaml、UVM 环境，因此需要同时证明 core TB 和 UVM TB 都还能跑最小 smoke。
- `hello-world` 是最小、最快、最容易定位问题的 sanity test。

实现方式：

- workflow 放在 `cv32e20-dv/.github/workflows/cv32e20-dv-ci.yml`。
- `core-hello-world` 使用 GitHub-hosted Ubuntu runner、Verilator v5.046 和 RISC-V GCC。
- `uvm-hello-world` 使用 self-hosted runner matrix：
  - `vsim`：需要 Questa 2023.3_2。
  - `dsim`：需要 DSim 2026。
- 两类 job 都上传 simulation results artifact。

### 4. Runner/tool 要求

Mike 列出的 runner 工具：

- full `riscv64-unknown-elf-*` toolchain
- Verilator v5.046
- UDB
- Sail

目的：

- RISC-V toolchain 用于构建 test program。
- Verilator v5.046 用于 open-source core TB 和 ACT4。
- Sail 是 ACT4 generation/reference flow 的依赖。
- UDB 是后续 debug/trace/coverage 工作流的重要依赖，当前 smoke job 先做可选检查，避免第一阶段被未定路径阻塞。

本次实现：

- `.github/actions/setup-cv32e20-tools/action.yml` 统一处理工具安装、缓存和 PATH/env。
- Verilator 默认版本固定为 `5.046`。
- RISC-V toolchain 支持两种方式：runner 已安装，或通过 tarball URL 安装，也可 fallback 到 Ubuntu package。
- Sail 支持 runner 已安装，或通过 `SAIL_RISCV_TARBALL_URL` 安装。
- UDB 通过 `require-udb` 参数控制是否强制检查。

## 推荐启用顺序

1. 先把 `cv32e20-dv` 的 `dev` 与 `main` 同步，确认分支策略。
2. 在 `cv32e20-dv` 私有镜像仓库先启用 `core-hello-world / verilator`。
3. 配置 Questa/DSim self-hosted runner labels 和 license 环境。
4. 启用 UVM matrix。
5. 把 `cve2-ci-template/cve2-act-ci.yml` 复制到 `cve2` 仓库并验证一个小 PR。
6. 启用 dashboard，把 workflow 结果长期保存到 data branch 并发布到 GitHub Pages。

## 风险与待确认项

- Questa/DSim runner label 当前按 `[self-hosted, linux, questa]` 和 `[self-hosted, linux, dsim]` 编写，需要 Mike 或 infra 确认。
- UDB 的安装路径、license 变量、是否需要参与第一阶段 smoke，仍需确认。
- Sail v0.10 的二进制 tarball URL 需要在仓库变量或 runner 环境中提供，除非 runner 已预装。
- `cve2` workflow 必须落在 `cve2` 仓库，不能直接在 `cv32e20-dv` 仓库中作为正式 workflow 启用。
