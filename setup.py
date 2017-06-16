from setuptools import setup

f = open("README.rst")
try:
    try:
        readme_content = f.read()
    except:
        readme_content = ""
finally:
    f.close()

setup(
    name='restea',
    packages=['restea', 'restea.adapters'],
    version='0.3.5',
    description='Simple RESTful server toolkit',
    long_description=readme_content,
    author='Walery Jadlowski',
    author_email='bodb.digr@gmail.com',
    url='https://github.com/bodbdigr/restea',
    keywords=['rest', 'restful', 'restea'],
    install_requires=[
        'future==0.16.0',
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pytest-mock',
    ],
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
