sudo apt-get update
sudo apt-get upgrade
sudo apt-get install git
sudo apt-get install git-lfs
chmod +x ./setup_git_lfs.sh
chmod +x ./dhusget.sh
git config credential.helper store
./setup_git_lfs.sh
touch secrets.py