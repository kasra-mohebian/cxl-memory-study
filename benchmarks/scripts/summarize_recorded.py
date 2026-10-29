from pathlib import Path
import pandas as pd
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
if args.out.exists(): parser.error('Output already exists')
r=Path(__file__).resolve().parents[2];records=[]
for name, groups, metrics in [
 ('memory_benchmark',['tier'],['write_gbs','read_gbs']),
 ('page_benchmark',['tier'],['seq_page_mpps','rand_page_mpps']),
 ('page_copy_benchmark',['tier'],['seq_copy_gbs','rand_copy_gbs']),
 ('inter_tier_copy_benchmark',['src_tier','dst_tier'],['seq_copy_gbs','rand_copy_gbs']),
 ('page_copy_size_sweep',['tier','size_mb'],['seq_copy_gbs','rand_copy_gbs'])]:
 df=pd.read_csv(r/f'benchmarks/results/{name}.csv')
 for key,g in df.groupby(groups):
  key=key if isinstance(key,tuple) else (key,)
  for metric in metrics:
   v=g[metric];records.append({'experiment':name,'group':' / '.join(map(str,key)),'metric':metric,'n':len(v),'mean':v.mean(),'median':v.median(),'min':v.min(),'max':v.max(),'sample_sd':v.std()})
out=args.out.parent;out.mkdir(parents=True,exist_ok=True)
pd.DataFrame(records).to_csv(args.out,index=False,float_format='%.10g')
