from setuptools import setup, find_packages
setup(
    name='cgePy',
    version='0.1.0',
    author='CyrSol',
    author_email='cyrille.soliman@gmail.com',
    url='https://github.com/CyrSol/CardGameEngine',
    package=find_packages(),
    readme = 'README.md',
    install_requires=[
        'Pygame'
    ]
)