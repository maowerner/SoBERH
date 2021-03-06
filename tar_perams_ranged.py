#!/usr/bin/python

# Small bash script to tar perambulators in packages of configurations
import argument_parsing as ap
import sys, os, tarfile, re, subprocess

def main():
    parser = ap.arg_parser()
    args = parser.parse_args()
    ens = args.ens
    flv = args.flv

    otf = args.otf

    d = args.delta_config
    size = args.chunksize

    USER = args.USER
    HOST = args.HOST

    SRC = args.SRC
    WRK = args.WRK
    SNC = args.SNC

    # Set default for WRK and SNC depending on ens and flv
    if WRK is None:
      WRK='/hiskp2/werner/peram_vault/'+ens+'/'+flv+'/'
    try:
       if not os.path.exists(os.path.dirname(WRK)):
           os.makedirs(os.path.dirname(WRK))
    except OSError as err:
       print(err)
    if SNC is None:
      SNC='/arch/hch02/hch026/LapH_perambulators/'+ens+'/'+flv+'/'

    ################################################################################

    # create a list of configs to tar, add one config in the end because python
    cfg_want = ['cnfg%04d' % c for c in range(args.first_config, args.final_config+1,int(d))]

    # Function sorting by digits independent from length
    def natural_sort(l): 
      convert = lambda text: int(text) if text.isdigit() else text.lower() 
      alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
      return sorted(l, key = alphanum_key)

    # cut a list of configuration based on indices
    def cut_range(lst, rnge):
      # the indices pointing to first and last index
      #TODO: think about list comprehension
      #e = [i for i,s in enumerate(lst) if]
      b, e = 0, 0
      for i, s in enumerate(lst):
      # s is padded with cnfg, exclude from comparison for identity checking
        if rnge[0] == s[4:]:
          b = i
        if rnge[1] == s[4:]:
          e = i
      res = lst[b:e+2]
      #return res[0::int(rnge[2])]
      return res[0::2]

    # check wether all configurations are there
    # get names
    cfg_have = os.listdir(SRC)
    # test and sort list
    # regular expression containing "cnfg" followed by at least one int
    reg = re.compile(r'cnfg\d+')
    cfgs_reg = filter(reg.match, cfg_have)
    cfgs_new = natural_sort(cfgs_reg)

    # Restrict cfgs_want to the subset we have and print all configurations in 
    # cfg_want but not in cfg_have
    for c in natural_sort(set(cfg_want) - set(cfg_have)):
      print 'Skipping configuration ', c
    cfgs_cut = set(cfg_want).intersection(cfg_have)

    # sort intersection
    cfgs_tar = natural_sort(cfgs_cut)
    print 'Archiving: ', cfgs_tar

    # chunks for taring
    chunks = [cfgs_tar[i:i+size] for i  in range(0, len(cfgs_tar), size)]
    EXCLUDE_FILES=['main']
    arclist = []
    for c in chunks:
      b=c[0]
      e=c[-1]
      # distance in filename from interval
      # First create a list with the according configurations
      
      os.chdir(SRC)
      # Now we want to tar everything in the range list into one specific tar archive
      arcname=WRK+'perams_' +b[4:] + '-' + str(d) + '-' +e[4:]+ '.tar'
      if os.path.isfile(arcname) is False:
        with tarfile.open(arcname,"w",dereference=True) as tar:
          for name in c:
            tar.add(name,filter=lambda x: None if x.name in EXCLUDE_FILES
                else x)
      else:
        print 'Archive already exists. Did not write!'
      
      # if "on the fly archival" is disabled, we will transfer all
      # files in one big sweep later and not delete them 
      if otf is False:
        arclist.append(arcname)
      else:  
      # on the fly archival to save space
        rsync_args=['rsync', arcname, USER+'@'+HOST+':'+SNC]
        rval=subprocess.call(rsync_args)
        # delete file if rsync was successful
        if rval == 0:
          os.remove(arcname)

    ## Rsync perambulator archive to destination
    if otf is False:
      for name in arclist:
        rsync_args=['rsync', name, USER+'@'+HOST+':'+SNC]
        subprocess.call(rsync_args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
