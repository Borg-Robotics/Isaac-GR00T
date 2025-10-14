# Brev Setup

![](img/brev_interface.png)

Go to [https://brev.nvidia.com/](https://brev.nvidia.com/) -> Sign up / Log in.

Create new instance -> Select GPU (A100) -> Select model (all similar) -> click VM Mode w/ Jupyter -> Custom Container -> Docker image: `pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel` -> Deploy -> Wait.

Replace `awesome-gpu-name` with your instance name and run:
```shell
brev shell awesome-gpu-name
```

Clone the repo and enter it:
```shell
cd /workspace
git clone https://github.com/Borg-Robotics/Isaac-GR00T.git
cd Isaac-GR00T
```

Run the setup script:
```shell
source ./brev/cloud_setup.bash
```