""" IoT Home Page 

Página inicial do Piloto IoT Dashboard.

"""

import streamlit as st
import argparse
import os

# Get aws_access_key_id and aws_secret_access_key
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='IoT Dashboard',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--aws_access_key_id',
                        action='append',
                        help='AWS account access key',
                        metavar='str',
                        default=None)
        
    parser.add_argument('--aws_secret_access_key',
                        action='append',
                        help='AWS account secret access key',
                        metavar='str',
                        default=None)
    
    try: 
        args = parser.parse_args()
    except SystemExit as e:
        # This exception will be raised if --help or invalid command line arguments
        # are used. Currently streamlit prevents the program from exiting normally
        # so we have to do a hard exit.
        os._exit(e.code)

    return args

args = get_args()

if args.aws_access_key_id == None or args.aws_secret_access_key == None:
    st.write ("aws_access_key_id and aws_secret_access_key are required parameters.")
    exit()
else:
    if "aws_access_key_id" not in st.session_state:
        st.session_state['aws_access_key_id'] = args.aws_access_key_id[0]
    if "aws_secret_access_key" not in st.session_state:
        st.session_state['aws_secret_access_key'] = args.aws_secret_access_key[0]

st.set_page_config(
    page_title="Dashboard IoT",
    page_icon="🔍",
)

st.write("# Bem vindo ao Dashboard IoT 🔍")

st.markdown(
    """
    Página inicial do Dashboard IoT

""", unsafe_allow_html=True
)
