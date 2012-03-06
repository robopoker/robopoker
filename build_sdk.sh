mkdir mkdist_tmp
python setup.py sdist
mv dist/*.zip mkdist_tmp/
rm -r dist

FNAME=`find mkdist_tmp/*.zip`
FNAME=${FNAME//src/win}

python setup.py py2exe
rm dist/*.sh
sed -i 's/python platform.py/platform.exe/g' dist/*.bat
zip -r $FNAME dist

rm -r dist
rm -r build
mv mkdist_tmp dist