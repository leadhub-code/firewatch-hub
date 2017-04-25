from setuptools import setup, find_packages

setup(
    name='firewatch-hub',
    version='0.0.1',
    description='Log monitoring for error and warning messages',
    url='https://github.com/leadhub-code/firewatch-hub',
    author='Petr Messner',
    author_email='petr.messner@gmail.com',
    license='MIT',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        #'Intended Audience :: Developers',
        #'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='log monitoring errors warnings',
    packages=find_packages(exclude=['doc*', 'test*']),
    install_requires=[
        'flask',
    ],
    extras_require={
        #'dev': ['check-manifest'],
        #'test': ['coverage'],
    },
)
