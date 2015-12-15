from distutils.core import setup


setup(
    name='restea',
    packages=['restea', 'restea.adapters'],
    version='0.2.2',
    description='Simple RESTful server toolkit',
    author='Walery Jadlowski',
    author_email='bodb.digr@gmail.com',
    url='https://github.com/bodbdigr/restea',
    download_url='https://github.com/bodbdigr/restea/archive/0.2.2.tar.gz',
    keywords=['rest', 'restful', 'restea'],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
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
