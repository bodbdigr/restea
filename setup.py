from setuptools import setup

readme_content = ''
with open("README.rst") as f:
    readme_content = f.read()

setup(
    name='restea',
    packages=['restea', 'restea.adapters'],
    version='0.3.12',
    description='Simple RESTful server toolkit',
    long_description=readme_content,
    author='Walery Jadlowski',
    author_email='bodb.digr@gmail.com',
    url='https://github.com/bodbdigr/restea',
    keywords=['rest', 'restful', 'restea'],
    install_requires=[
        'six==1.16.0',
    ],
    tests_require=[
        'pytest==4.6.11',
        'pytest-cov==2.12.0',
        'pytest-mock==2.0.0',
        'mock==3.0.5',
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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
