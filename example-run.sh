#!/bin/bash
hashes=(pcg_linear2
pcg_nested2
pcg_lcgcombine2
)

width=128
height=128
depth=1
trength=1

for HASH in ${hashes[@]} ;
do
    echo ${HASH}

    for i in 2 3 4 5 6 7 8 ;
    do
	    echo $i

        j=${i}
        k=1
        l=1

        for run in 1 2 3 4 5 6 7 8 9;
        do
	        echo run${run}

            mkdir -p results/${width}x${height}x${depth}x${trength}/${i}x${j}x${k}x${l}/run${run}

	    ./hashtable-test -w $width -h $height -d $depth -t $trength -i $i -j $j -k $k -l $l -r $HASH > results/${width}x${height}x${depth}x${trength}/${i}x${j}x${k}x${l}/run${run}/${HASH}.txt
	done
    done
done
