__NOTE: this uses a woefully out of date Riak installation,
and is just sticking around on github for posterirty at the moment__

___


# Riak EC2 Cluster Launcher


## Dependencies
`launch.py` is a simple Python script to launch an `N`-node Riak cluster. The requirements can be installed
with:

    sudo pip install fabric paramiko boto

To run the command you will also need an EC2 account, and your environment variables set as described
[here](http://code.google.com/p/boto/wiki/BotoConfig).

## Usage

    # key_filename is the name of an EC2 Key Pair
    # key_filepath is the full path to the private key
    # for the key in key_filepath
    # The key will be used to ssh into the master node,
    # and wait for Riak to be running
    ./launch.py key_filename key_filepath user_data.sh 100

## Limitations

Each machine will download Riak application configuration from an s3 bucket that I personally own.
If you really wanted to be secure, you would copy this config to a server that you control, or
just use `sed` or something and edit the app defaults from `user_data.sh`.
