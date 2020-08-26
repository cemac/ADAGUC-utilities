#! /bin/bash

export NWCSAF2ADAGUC_PATH=/home/adaguc/NWCSAF2ADAGUC
export USER="adaguc"

lockfile=$NWCSAF2ADAGUC_PATH/blocked.by.dbupdt
dirlog=$NWCSAF2ADAGUC_PATH/logs
if [ ! -d "$dirlog" ] ; then mkdir -p "$dirlog" && echo 0 > $dirlog/counter.txt ; fi
if [ -d "$dirlog" ] && [ ! -f $dirlog/counter.txt ] ; then echo 0 > $dirlog/counter.txt ; fi

pypid=`ps -fu $USER | fgrep "python3 $NWCSAF2ADAGUC_PATH/updater.py" | grep -v grep | awk '{print$2}'`
if [ -n "$pypid" ]
then
	echo
	date
	echo "There is another updater.py running: $pypid"
	count=`awk -F, '{printf("%d\n",$1+1)}' $dirlog/counter.txt`
	echo $count > $dirlog/counter.txt
	echo $count
	if test "$count" = 5
	then
		echo "It has been running for the last 5 minutes. Process killed: $pypid"
		echo "updater.py started"
		echo
		/bin/kill -9 $pypid
		if [ -f $lockfile ]; then rm $lockfile; fi

		echo 0 > $dirlog/counter.txt
		python3 $NWCSAF2ADAGUC_PATH/updater.py
	fi
	echo
	exit 0
else
	count=`awk -F, '{printf("%d\n",$1)}' $dirlog/counter.txt`
	if test "$count" != 0 ; then echo 0 > $dirlog/counter.txt ; fi
	python3 $NWCSAF2ADAGUC_PATH/updater.py
fi
exit 0
