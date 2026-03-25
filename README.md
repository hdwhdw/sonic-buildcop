# 🔧 sonic-buildcop

**Build health tools for [sonic-net](https://github.com/sonic-net) repositories**

[![Submodule Status](https://img.shields.io/badge/submodule_status-live-blue)](https://hdwhdw.github.io/sonic-buildcop/)

## Projects

| Project | Description | Live |
|---|---|---|
| [`submodule-status/`](submodule-status/) | Tracks submodule pointer staleness in sonic-buildimage | [Dashboard](https://hdwhdw.github.io/sonic-buildcop/) |

## submodule-status

sonic-buildimage uses dozens of Git submodules. A bot ([mssonicbld](https://github.com/mssonicbld)) submits PRs to keep pointers current, but they still fall behind — sometimes by weeks.

This tool monitors submodule staleness and publishes a dashboard to GitHub Pages.

👉 **[View the live dashboard](https://hdwhdw.github.io/sonic-buildcop/)**

## License

MIT
