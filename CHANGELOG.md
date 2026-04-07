# Changelog

## [0.1.1](https://github.com/KinjiKawaguchi/nodiscard/compare/v0.1.0...v0.1.1) (2026-04-07)


### Bug Fixes

* eliminate false positives and negatives in type inference ([#2](https://github.com/KinjiKawaguchi/nodiscard/issues/2)) ([3324150](https://github.com/KinjiKawaguchi/nodiscard/commit/3324150f4242ddda3a3a4413b6699469e22de3ed))

## 0.1.0 (2026-04-06)


### Features

* add [@nodiscard](https://github.com/nodiscard) decorator, NoDiscard marker, and data models ([ac68719](https://github.com/KinjiKawaguchi/nodiscard/commit/ac68719f37e892254715d7aab6ae84bdd0b4f54d))
* add checker facade for orchestrating the analysis pipeline ([97c5bab](https://github.com/KinjiKawaguchi/nodiscard/commit/97c5bab7af52a01ad9b6624943b2f03b4f2249ce))
* add CLI entry point with text/json output and pyproject.toml config ([56a9a93](https://github.com/KinjiKawaguchi/nodiscard/commit/56a9a930f74c20d442fa01a60f3d5490a8e8e8d3))
* add collector, type tracker, import resolver, and detector ([1e0caff](https://github.com/KinjiKawaguchi/nodiscard/commit/1e0caff965eab793bbf93b208cad24bb5192ff26))


### Bug Fixes

* **ci:** trigger CI on all pull requests including Release Please ([2c4c5ff](https://github.com/KinjiKawaguchi/nodiscard/commit/2c4c5ff3ccea11f2cc87603af316891b6c8c1dbc))
* **ci:** use setup-uv@v7 (v8 major tag not yet available) ([fac672e](https://github.com/KinjiKawaguchi/nodiscard/commit/fac672efd03fa5322d6dcacc4763acd754e9d6de))
* resolve re-export detection by recursively walking import chains ([949cf6d](https://github.com/KinjiKawaguchi/nodiscard/commit/949cf6d064522248e593c3d3986d53030a3a991c))
* resolve ty typecheck errors in _marker.py and cli.py ([f7b25d7](https://github.com/KinjiKawaguchi/nodiscard/commit/f7b25d79cc3e0dfa279c58d10decb4dab2543ad6))


### Documentation

* add DeepWiki link to Contributing section ([5e5842c](https://github.com/KinjiKawaguchi/nodiscard/commit/5e5842c0248e48f1a85839f574148eb5f87e5747))
* add project spec, test cases, and CLAUDE.md instructions ([41b5b7a](https://github.com/KinjiKawaguchi/nodiscard/commit/41b5b7afe5332541312665fe4feb51681081d4b1))
