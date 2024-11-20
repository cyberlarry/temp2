from bitcoinlib.keys import Key
from itertools import count
import os, multiprocessing, argparse, paramiko
from datetime import datetime


def generate_db(core, btc_address_queue):
    for iteration in count(1):
        # Generate private + public keys and btc address
        key = Key()
        gen_keypair = key.address() + "," + key.wif()  # create csv string
        btc_address_queue.put(gen_keypair)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--cores",
        default=8,
        type=int,
        help="Number of CPU cores to use (default: 4)",
    )

    # setup queues
    args = parser.parse_args()
    cores = args.cores
    # create multicore queue
    btc_address_queue = multiprocessing.Queue()

    # restart handling, check for existing files and start at end
    file_count = 0
    # get number of files in directory, failback to 0
    try:
        for filename in os.listdir('./db'):
            file_count += 1
    except ValueError:
        file_count = 0
    except FileNotFoundError:
        os.makedirs('./db')

    print('Starting database file count: ', file_count)
    print('Executing generation with', cores, 'cores active')

    # call generate_db and listen to keyboard interrupt
    try:
        for core in range(cores):
            process = multiprocessing.Process(target=generate_db, args=(core, btc_address_queue))
            process.start()

        while True:
            # set up next iteration of logfile
            filename = "./db/db" + str(file_count) + ".csv"  # create filename string
            wallet_file = open(filename, "a")  # create new file
            start_time = datetime.today().timestamp()  # reset start time

            for i in range(1000000):
                keypair = btc_address_queue.get()
                wallet_file.write(keypair + "\n")  # write line to file

            wallet_file.close()  # close current file
            file_count += 1  # file completed, increase to next number
            time_diff = datetime.today().timestamp() - start_time
            print("Genereated 1mil address/wif pairs in ", time_diff)

            # upload generated db file to destination
            localpath = filename
            remotepath = "/home/neo/btc-db-temp"

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname="m.jollymuffin.top", username="mouse", password="")
            sftp = ssh.open_sftp()
            sftp.put(localpath, remotepath)
            # sftp.close()
            ssh.close()

            # delete local file
            oldfile = "./db/db" + str(file_count - 1) + ".csv"
            # os.remove(oldfile)

    except KeyboardInterrupt:
        print("Interrupt received, aborting current file and quitting program")
        exit(1)
