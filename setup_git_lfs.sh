git lfs install
git lfs track '*.zip'
git add .gitattributes "*.zip"
git commit -m "add gitattributes for lfs"
git lfs migrate import --include="*.zip"
git push