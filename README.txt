Readme
==============================================================================

The mturkweb package is a simple Amazon Mechanical Turk (AMT) library for 
retrieving information about batches that were created in the AMT web interface.


Usage
------------------------------------------------------------------------------

The mturkweb package provides an MTurkWebSession class which can be used to
retrieve information about batches. An instance of this class is created 
by calling the login function with the credentials of a Mechanical Turk 
requester account.

Example usage:

::

    import mturkweb
    
    session = mturkweb.login('user@email.example', 'password')
    batches = session.get_batches()
    
    for status in batches:
        print status
        print '-' * 76
        
        for batch in batches[status]:
            print '%s\t%s' % (batch.geturl(), batch.name)
        
        print
        print



Installation
------------------------------------------------------------------------------

This package can be installed using `pip`:

::

    pip install https://github.com/ShinNoNoir/mturkweb/archive/master.zip



