cd ..
gitingest -e ".pytest_cache\" -e "arduino_firmware[DEPRECATED]\" -e "config\__pycache__\" -e "data\" -e "src\__pycache__\" -e "tests\__pycache__\" -e "v2\" -e "raw.csv" -e "reference\"
tree /f /a > tree.txt
cd .\runners\ 