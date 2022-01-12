import os
import math
import h5py
import modisco
import pandas as pd
import numpy as np
from modisco.visualization import viz_sequence
import matplotlib
matplotlib.use('pdf')
from matplotlib import pyplot as plt
import argparse

pd.options.display.max_colwidth = 500

def fetch_viz_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--modisco_h5py", required=True, type=str, help="path to the output .h5py file generated by the run_modisco.py script")
    parser.add_argument("-t", "--tomtom_tsv", required=True, type=str, help="path to the tsv generated by fetch_tomtom.py")
    parser.add_argument("-o", "--output_dir", type=str, required=True, help="Path to store the output - modisco logos and html")
    parser.add_argument("-vd", "--vier_db", type=str, required=True, help="Path to vierstra logos db")
    parser.add_argument("-th", "--trim_threshold", type=float, default=0.3, help="Trim threshold for trimming long motif, trim to those with at least prob trim_threshold on both ends")
    parser.add_argument("-hl", "--html_link", type=str, required=True, help="link to use for htmls - will be used as html_link/modisco_logos/ for modisco and html_link/vierstra_logos/ for vierestra")   
    parser.add_argument("-vhl", "--vir_html_link", type=str, required=True, help="link to use for svierestra html")   
    parser.add_argument("-s", "--score_type", type=str, required=True, help="profile/counts")   
    parser.add_argument("-d", "--meme_motif_db", required=True, type=str, help="path to motif database")
    args = parser.parse_args()
    return args

def path_to_image_html(path):
    return '<img src="'+ path + '" width="240" >'

def _plot_weights(array,
                  path,
                  figsize=(10,3),
                 **kwargs):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111) 
    viz_sequence.plot_weights_given_ax(ax=ax, array=array,**kwargs)
    plt.savefig(path)
    plt.close()
    
def make_logo(match, logo_dir_vier, meme_motif_db):
    background = np.array([0.25, 0.25, 0.25, 0.25])

    if match + '.png' in os.listdir(logo_dir_vier):
        pass
    elif match + '.pfm' in os.listdir(meme_motif_db):
        ppm = np.loadtxt(os.path.join(meme_motif_db, match + '.pfm'), delimiter='\t')
        ppm = np.transpose(ppm)
        _plot_weights(viz_sequence.ic_scale(ppm, background=background),
                        path=logo_dir_vier + '/' + match + '.png')
        

def create_modisco_logos(modisco_file,modisco_logo_dir, trim_threshold, score_type):
    hdf5_results = h5py.File(modisco_file,'r')
    i=0
    for metacluster_name in hdf5_results["metacluster_idx_to_submetacluster_results"]:
        metacluster = hdf5_results["metacluster_idx_to_submetacluster_results"][metacluster_name]
        #if metacluster['activity_pattern'][0] == 1:
        if 1:
            all_pattern_names = [x.decode("utf-8") for x in list(metacluster["seqlets_to_patterns_result"]["patterns"]["all_pattern_names"][:])]
            for pattern_name in all_pattern_names:
                cwm_fwd = np.array(metacluster['seqlets_to_patterns_result']['patterns'][pattern_name]['task0_contrib_scores']['fwd'])
                cwm_rev = np.array(metacluster['seqlets_to_patterns_result']['patterns'][pattern_name]['task0_contrib_scores']['rev'])

                score_fwd = np.sum(np.abs(cwm_fwd), axis=1)
                score_rev = np.sum(np.abs(cwm_rev), axis=1)

                trim_thresh_fwd = np.max(score_fwd) * trim_threshold
                trim_thresh_rev = np.max(score_rev) * trim_threshold

                pass_inds_fwd = np.where(score_fwd >= trim_thresh_fwd)[0]
                pass_inds_rev = np.where(score_rev >= trim_thresh_rev)[0]

                start_fwd, end_fwd = max(np.min(pass_inds_fwd) - 4, 0), min(np.max(pass_inds_fwd) + 4 + 1, len(score_fwd) + 1)
                start_rev, end_rev = max(np.min(pass_inds_rev) - 4, 0), min(np.max(pass_inds_rev) + 4 + 1, len(score_rev) + 1)

                trimmed_cwm_fwd = cwm_fwd[start_fwd:end_fwd]
                trimmed_cwm_rev = cwm_rev[start_rev:end_rev]

                pattern_name_new='pattern_' + str(i)
                i+=1
                _plot_weights(trimmed_cwm_fwd,
                        path=modisco_logo_dir + '/' + score_type + '.' + pattern_name_new + '.cwm.fwd.png')
                _plot_weights(trimmed_cwm_rev,
                        path=modisco_logo_dir + "/" + score_type + '.' + pattern_name_new + '.cwm.rev.png')


if __name__=="__main__":

    args = fetch_viz_args()

    score_type=args.score_type
    # make modisco_logos directory and make trimmed modisco logos for viz

    if not os.path.isdir(args.output_dir + '/' + "modisco_logos/"):
        os.mkdir(args.output_dir + '/' + "modisco_logos/")
    modisco_logo_dir=args.output_dir + '/' + "modisco_logos/"

    create_modisco_logos(args.modisco_h5py, modisco_logo_dir, args.trim_threshold, score_type)

    tomtom_df = pd.read_csv(args.tomtom_tsv, sep='\t')
    tomtom_df['modisco_cwm_fwd'] = [args.html_link + '/modisco_logos/' + score_type + '.pattern_' + str(i) + '.cwm.fwd.png' for i in range(len(tomtom_df))]
    tomtom_df['modisco_cwm_rev'] = [args.html_link + '/modisco_logos/' + score_type + '.pattern_' + str(i) + '.cwm.rev.png' for i in range(len(tomtom_df))]
    
    logo_dict = {x: [] for x in range(1,11)}

    for index, row in tomtom_df.iterrows():
        for i in range(1,11):
            if not pd.isnull(row['Match_' + str(i)]):
                make_logo(row['Match_' + str(i)], args.vier_db, args.meme_motif_db)
                logo_dict[i].append(args.vir_html_link +  row['Match_' + str(i)] + '.png')
            else:
                logo_dict[i].append('NA')

    for i in range(1,11):
        tomtom_df['match' + str(i) + '_logo'] = logo_dict[i]

    tomtom_df.columns = ['pattern', 'num_seqlets',
                            'match0', 'qval0', 'match1', 'qval1',
                            'match2', 'qval2', 'match3', 'qval3',
                            'match4', 'qval4', 'match5', 'qval5',
                            'match6', 'qval6', 'match7', 'qval7',
                            'match8', 'qval8', 'match9', 'qval9',
                            'modisco_cwm_fwd', 'modisco_cwm_rev',
                            'match0_logo', 'match1_logo', 'match2_logo', 'match3_logo',
                            'match4_logo', 'match5_logo', 'match6_logo', 'match7_logo',
                            'match8_logo', 'match9_logo']

    tomtom_df = tomtom_df[['pattern',
                            'num_seqlets', 'modisco_cwm_fwd', 'modisco_cwm_rev',
                            'match0', 'qval0', 'match0_logo', 'match1', 'qval1', 'match1_logo',
                            'match2', 'qval2', 'match2_logo', 'match3', 'qval3', 'match3_logo',
                            'match4', 'qval4', 'match4_logo', 'match5', 'qval5', 'match5_logo',
                            'match6', 'qval6', 'match6_logo', 'match7', 'qval7', 'match7_logo',
                            'match8', 'qval8', 'match8_logo', 'match9', 'qval9', 'match9_logo',
                            ]]           

    tomtom_df.to_html(open(os.path.join(args.output_dir,score_type + '.motifs.html'), 'w'),
                    escape=False, formatters=dict(modisco_cwm_fwd=path_to_image_html,
                                                 modisco_cwm_rev=path_to_image_html,
                                                 match0_logo=path_to_image_html,
                                                 match1_logo=path_to_image_html,
                                                 match2_logo=path_to_image_html,
                                                 match3_logo=path_to_image_html,
                                                 match4_logo=path_to_image_html,
                                                 match5_logo=path_to_image_html,
                                                 match6_logo=path_to_image_html,
                                                 match7_logo=path_to_image_html,
                                                 match8_logo=path_to_image_html,
                                                 match9_logo=path_to_image_html
                                                 ), index=False)


print(tomtom_df.head())


