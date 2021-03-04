#!/bin/bash

# this installs the virtualenv module
python3.7 -m pip install virtualenv

# this cd to your root directory and install a virtual environment named gym_venv
cd
python3.7 -m venv gym_venv
dir=$(pwd)
# activate the created virtual environment 
source gym_venv/bin/activate
# go back to the previous directory
cd -
# and copy requirements.txt to the venv directory
cp requirements.txt ~/gym_venv/.
# and then cd back to the venv
cd $dir/gym_venv/
# and then the real pip here is the bin/pip
pip_env=$dir/gym_venv/bin/pip
python_env=$dir/gym_venv/bin/python3
# update pip
$pip_env install -U pip
# then write to ~/.bashrc and ~/.bash_profile that gym_venv from now on is to activate the
# virtual environment
echo "alias gym_venv='source ~/gym_venv/bin/activate'" >> ~/.bashrc
echo "alias gym_venv='source ~/gym_venv/bin/activate'" >> ~/.bash_profile
source ~/.bashrc
source ~/.bash_profile
# and install the required python packages to the virtual environment
for line in $(cat requirements.txt)
do
    $python_env -m pip install $line
done

echo created gym environment
# now go back to the previous directory
cd -
