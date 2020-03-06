from distutils.core import setup

setup(name='mouseberry',
      version='0.2',
      description='Hackable behavior controller for RPi',
      author='Michael B.F. Lynn',
      author_email='micllynn@gmail.com',
      url='https://github.com/micllynn/mouseberry/',
      license='MIT',
      packages='mouseberry',
      install_requires=['python>=3.6',
                        'numpy',
                        'scipy',
                        'h5py>=2.10.0',
                        'RPi',
                        'paramiko'])
