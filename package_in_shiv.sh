python setup.py sdist bdist_wheel

shiv --site-packages dist --compressed -o bin/AutoBiller.pyz -e AutoBiller.__main__:main . -r requirements.txt

