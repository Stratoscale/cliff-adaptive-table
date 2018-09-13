from setuptools import setup, find_packages

setup(
    name='cliff-adaptive-table',
    git_version=True,

    description='adaptive_table for cliff',
    long_description='an adaptive table formatter for cliff',

    author='Lior Segev',
    author_email='lior@stratoscale.com',

    url='https://stratoscale.com/',

    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: Apache Software License',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.2',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=['cliff_adaptive_table'],
    install_requires=[],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,
    package_data={},
    entry_points={
        'cliff.formatter.list': [
            'adaptive_table = cliff_adaptive_table.cliff_adaptive_table:AdaptiveTableFormatter',
        ],
        'cliff.formatter.show': [
            'adaptive_table = cliff_adaptive_table.cliff_adaptive_table:AdaptiveTableFormatter',
        ],
    },
)
