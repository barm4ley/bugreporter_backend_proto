import os


def make_metadata_file(metadata, meta_dir, meta_file='metadata.pl'):
    meta_str =\
'''
$VAR1 = {{
          'sVersion' => '{version}',
          'description' => '{description}',
          'sBugTypeID' => '{bug_type_id}',
          'sCustomerEmail' => '{customer_email}',
          'sTitle' => '{title}',
          'sComputer' => '{computer}',
          'timestamp' => '{timestamp}',
          'sBugReproducibility' => '{bug_reproducibility}',
          'MD5' => undef
         }};
'''.format(**metadata)

    full_name = os.path.join(meta_dir, meta_file)

    with open(full_name, 'ab') as ofile:
        ofile.write(str.encode(meta_str))

    return meta_str
