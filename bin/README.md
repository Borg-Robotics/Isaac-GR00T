# Brev Setup

Create new instance -> Select GPU (A100) -> Select model (all similar) -> click VM Mode w/ Jupyter -> Custom Container -> Docker image: `pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel` -> Deploy -> Wait.

```shell
brev shell awesome-gpu-name
```

Clone the repo:
```shell
git clone https://github.com/Borg-Robotics/Isaac-GR00T.git
```

Enter the repo:
```shell
cd Isaac-GR00T
```

Run the setup script:
```shell
./bin/cloud_setup.bash
```