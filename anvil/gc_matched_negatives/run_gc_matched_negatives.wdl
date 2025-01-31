version 1.0

task run_gc_matched_negatives {
	input {
		String experiment
		File reference_file
		File chrom_sizes
		File blacklist
		File peaks
		File reference_gc_hg38_stride_50_flank_size_1057
  	}	
	command {
		#create data directories and download scripts
		cd /; mkdir my_data
		cd /my_data
		git clone https://github.com/kundajelab/chromatin-atlas-anvil.git
		chmod -R 777 chromatin-atlas-anvil
		cd chromatin-atlas-anvil/anvil/gc_matched_negatives/

		##outlier_detection

		echo "bash gc_negatives.sh" ${experiment} ${reference_file} ${chrom_sizes} ${blacklist}  ${peaks} ${reference_gc_hg38_stride_50_flank_size_1057} 
		
		bash gc_negatives.sh ${experiment} ${reference_file} ${chrom_sizes} ${blacklist} ${peaks} ${reference_gc_hg38_stride_50_flank_size_1057}

		echo "copying all files to cromwell_root folder"

		gzip /project/data/${experiment}_negatives_with_summit.bed
		
		cp /project/data/${experiment}_negatives_with_summit.bed.gz /cromwell_root/negatives_with_summit.bed.gz
		
	}
	
	output {
		File negatives_with_summit_bed = "negatives_with_summit.bed.gz"
	
	
	}

	runtime {
		docker: 'kundajelab/tf-atlas:gcp-gc-matched-negatives'
		memory: 100 + "GB"
		bootDiskSizeGb: 100
		disks: "local-disk 250 HDD"

	}
}

workflow gc_matched_negatives {
	input {
		String experiment
		File reference_file
		File chrom_sizes
		File blacklist
		File peaks
		File reference_gc_hg38_stride_50_flank_size_1057
	}

	call run_gc_matched_negatives {
		input:
			experiment = experiment,
			reference_file = reference_file,
			chrom_sizes = chrom_sizes,
			reference_gc_hg38_stride_50_flank_size_1057 = reference_gc_hg38_stride_50_flank_size_1057,
			peaks = peaks,
			blacklist = blacklist

 	}
	output {
		File negatives_with_summit_bed = run_gc_matched_negatives.negatives_with_summit_bed
		
	}
}
