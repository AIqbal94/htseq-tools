import os
import sys
import argparse

sys.stdout.flush()

parser = argparse.ArgumentParser()
parser.add_argument("-D", "--DAVID", help="Use this flag to perform DAVID GO enrichment analysis", action="store_true")
parser.add_argument("-i", "--inputFolder", help="Cuffdiff output folder")
parser.add_argument("-o", "--outputFolder", help="Output folder")
parser.add_argument("-G", "--originalGTF", help="Origianl/downloaded GTF")
parser.add_argument("-C", "--cuffcompareGTF", help="Merged cuffcompared GTF")
parser.add_argument("-f", "--inputFiles", help="Implies -s. Use this option to select which *.diff files you wish to analyse. Default: 'gene_exp.diff promoters.diff splicing.diff cds.diff isoform_exp.diff'.", default='gene_exp.diff promoters.diff splicing.diff cds.diff isoform_exp.diff')
parser.add_argument("-s", "--shortOutputName", help="Use this option to select a short outpput name for each *.diff file used in '-f'. Default: 'geneexp prom splic cds iso'.", default='geneexp prom splic cds iso')
parser.add_argument("--sigOnly", help="Only create report tables for cuffdiff-labeled significantly changed genes", action="store_true")
parser.add_argument("--description", help="Get a description of what this script does.", action="store_true")
parser.add_argument("--listMarts", help="List biomaRt Marts",action="store_true")
parser.add_argument("--mart", help="Your mart of choice. Default='ensembl'", default='ensembl')
parser.add_argument("--listDatasets", help="List datasets for your mart", action="store_true")
parser.add_argument("--dataset", help="Dataset of your choice. Default='celegans_gene_ensembl'", default='celegans_gene_ensembl')
parser.add_argument("--listFilters", help="List available filters", action="store_true")
parser.add_argument("--filter", help="Filter to use to identify your genes. Default='ensembl_gene_id'.", default='ensembl_gene_id')
parser.add_argument("--listAttributes", help="List available attributes for your dataset.", action="store_true")
parser.add_argument("--outputBiotypes", help="Outputs/attributes for your biotypes data. Default='ensembl_gene_id gene_biotype'. Order has to be kept, ie. first IDs then biotype.", default='ensembl_gene_id gene_biotype')
parser.add_argument("--outputGoterms", help="Outputs/attributes for your goterms data. Default='ensembl_gene_id go_id name_1006'. Order has to be kept, ie. 1st gene_id, then go_id, then go_term_name", default='ensembl_gene_id go_id name_1006')
parser.add_argument("--DAVIDid", help="DAVID's id for your dataset. List of ids available in http://david.abcc.ncifcrf.gov/content.jsp?file=DAVID_API.html#input_list. Default: 'WORMBASE_GENE_ID'", default='WORMBASE_GENE_ID')
parser.add_argument("-u", "--DAVIDuser", help="Your DAVID's user id. example: 'John.Doe@age.mpg.de'")
args = parser.parse_args()

if args.description:
    print "\nThis script annotates gene_exp.diff, promoters.diff, splicing.diff, cds.diff, and isoform_exp.diff cuffdiff tables. \
It generates 1 file for all results, 1 file for p<0.05, and 1 file/input table for q<0.05. \nFor significant values (i.e. q<0.05) it also generates \
tables containg all pair-wise comparisons in different sheets as well as gene ontology enrichment files for biological processes (BP), \
cellular component (CC), and molecular function (MF).\n \nRequired python packages:\na) pip install --user pandas==0.15.2 \nb) pip \
install --user numpy==1.9.2 \nc) pip install --user rpy2==2.5.6 \nd) pip install --user suds==0.4 \n \nRequired R packages: \nlibrary('biomaRt')\
 \n \nRequired arguments: \n-i, -o, -G, -C \n \nExample: \nannotate_cuffdiff_output.py -D -u John.Doe@age.mpg.de -i /path/to/cuffdiff_output_folder \
-G /path/to/original.gtf -C /path/to/merged_and_compared.gtf -o /path/to/python_output_folder\
\n\n*************************************\nDeveloped by Jorge Boucas at the group for Computational RNA Biology and Ageing of the Max Planck Institute for Biology of Ageing \n\njorge.boucas@age.mpg.de\n\n"
    sys.exit(0)


import pandas as pd
import numpy as np
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr


if args.listMarts:
    biomaRt = importr("biomaRt")
    print(biomaRt.listMarts())
    sys.exit(0)

if args.listDatasets:
    biomaRt = importr("biomaRt")
    ensemblMart=biomaRt.useMart(args.mart)
    print(biomaRt.listDatasets(ensemblMart))
    sys.exit(0)
                    
if args.listFilters:
    biomaRt = importr("biomaRt")
    ensemblMart=biomaRt.useMart(args.mart)
    ensembl=biomaRt.useDataset(args.dataset, mart=ensemblMart) 
    print(biomaRt.listFilters(ensembl))
    sys.exit(0)

if args.listAttributes:
    biomaRt = importr("biomaRt")
    ensemblMart=biomaRt.useMart(args.mart) 
    ensembl=biomaRt.useDataset(args.dataset, mart=ensemblMart)
    print(biomaRt.listAttributes(ensembl))
    sys.exit(0)

                    
print "\nInput folder: "+args.inputFolder
sys.stdout.flush()
print "Output folder: "+args.outputFolder
sys.stdout.flush()
print "Original GTF: "+args.originalGTF
sys.stdout.flush()
print "Cuffcompare curated GTF: "+args.cuffcompareGTF
sys.stdout.flush()
print "Files being analysed: "+args.inputFiles
sys.stdout.flush()
print "Short output labels: "+args.shortOutputName
sys.stdout.flush()

if args.sigOnly:
    print "\nReporting only significantly changed genes"
    sig_choice = ['yes']
    label_choice = ['diff_sig']
else:
    sig_choice = [0.05, 2, 'yes']
    label_choice = ['diff_p.05','diff_all','diff_sig']



if args.DAVID:
    print "\nPerforming DAVID GO enrichment analysis"
    print "\nYour DAVID user ID: "+args.DAVIDuser
else:
    print "\nUse -D if you want to perform DAVID GO enrichment analysis"

sys.stdout.flush()

in_files=args.inputFiles
in_files=in_files.split()

out_labels=args.shortOutputName
out_labels=out_labels.split()

out_biot=args.outputBiotypes
out_biot=out_biot.split()

out_go=args.outputGoterms
out_go=out_go.split()

############### Check available BioMart data ######################
#biomaRt = importr("biomaRt") # do not quote
#print(biomaRt.listMarts())
#ensemblMart=biomaRt.useMart(args.mart) # do not quote
#print(biomaRt.listDatasets(ensemblMart))
#ensembl=biomaRt.useDataset(args.dataset, mart=ensemblMart) # do not quote
#print(biomaRt.listFilters(ensembl))
#print(biomaRt.listAttributes(ensembl))
###################################################################

############### Set Biomart resources ######################
dataset = args.dataset
data_filter = args.filter # filter for gene_id in GTF file, 'link_ensembl_gene_id'
data_output_biotypes = out_biot # order needs to be kept i.e. id, biotype
data_output_goterms = out_go # order needs to be kept i.e. id, go_id, go_name
############################################################

############### Check DAVID's ID for your set ######################
# http://david.abcc.ncifcrf.gov/content.jsp?file=DAVID_API.html#input_list
DAVID_id=args.DAVIDid
####################################################################

################### paths to files #########################
diff_out = args.inputFolder
original_gtf = args.originalGTF
merged_fixed_gtf = args.cuffcompareGTF
python_output = args.outputFolder

if not os.path.exists(python_output):
    os.makedirs(python_output)

os.chdir(diff_out)

########## Get list of gene names and respective ids present in the data set

if os.path.isfile(python_output+'/genes_table.txt'):
    print "\nUsing already existing list of gene names and ids"
    sys.stdout.flush()
    genes=pd.read_table(python_output+'/genes_table.txt')
    genes = genes['g_id'].tolist()

else:
    print "\nGetting list of gene names and respective ids present in the data set"
    sys.stdout.flush()
    genes = pd.DataFrame()
    for file in ['gene_exp.diff', 'promoters.diff', 'splicing.diff', 'cds.diff', 'isoform_exp.diff']:
        df = pd.read_table(file)
        df = df[['gene']]
        genes = pd.concat([genes,df]).drop_duplicates()
    genes = genes.astype(str)
    genes = pd.DataFrame(genes.gene.str.split(',').tolist())[0]
    genes = genes.drop_duplicates()
    genes = genes.tolist()
    print "Imported list of differentially regulated genes"
    sys.stdout.flush()

    gtf = pd.read_table(original_gtf, sep='\t', skiprows=6, header=None, dtype=str)
    print "GTF imported"
    sys.stdout.flush()
    gtf = gtf.astype(str)

    gene_name = pd.DataFrame(gtf[8].str.split('gene_name').tolist())[1]
    gene_name = gene_name.astype(str)
    gene_name = pd.DataFrame(gene_name.str.split(';',1).tolist())
    gene_name = pd.DataFrame(gene_name[0].str.split('"').tolist())[1]
    gene_name = pd.DataFrame(gene_name)
    print "Read gene names from GTF"
    sys.stdout.flush()    

    gene_id = pd.DataFrame(gtf[8].str.split('gene_id').tolist())[1]
    gene_id = gene_id.astype(str)
    gene_id = pd.DataFrame(gene_id.str.split(';',1).tolist())
    gene_id = pd.DataFrame(gene_id[0].str.split('"').tolist())[1]
    gene_id = pd.DataFrame(gene_id)
    print "Read gene ids from GTF"
    sys.stdout.flush()
    
    name_id = pd.concat([gene_name, gene_id], axis=1).drop_duplicates()
    name_id.columns = ['g_name','g_id']
    name_id = name_id[name_id['g_name'].isin(genes)]
    print "Generated Names/IDs table"
    sys.stdout.flush()

    genes = name_id['g_id'].tolist()

    name_id.to_csv(python_output+'/genes_table.txt', sep="\t",index=False)

    del gtf, gene_name, gene_id, name_id


# Use R and BioMart to retrieve biotypes and gene ontoloty information

if os.path.isfile(python_output+'/biotypes_go_raw.txt'):
    print "\nUsing already existing biotypes_go_raw.txt file"
    sys.stdout.flush()
else:
    print "\nRetrieving biotypes and gene ontoloy information"
    sys.stdout.flush()
    biomaRt = importr("biomaRt")
    ensemblMart=biomaRt.useMart(args.mart)
    ensembl=biomaRt.useDataset(args.dataset, mart=ensemblMart)
    biotypes=biomaRt.getBM(attributes=data_output_biotypes, filters=data_filter, values=genes, mart=ensembl)
    goterms=biomaRt.getBM(attributes=data_output_goterms, filters=data_filter, values=genes, mart=ensembl)
    bio_go=robjects.r.merge(biotypes, goterms,by=1, all='TRUE')
    bio_go.to_csvfile(python_output+'/biotypes_go_raw.txt', quote=False, sep='\t', row_names=False)


# generate biotypes and go terms table using R/biomart output table.
                
if os.path.isfile(python_output+'/biotypes_go.txt'):
    print "\nUsing already existing biotypes_go.txt file"
    sys.stdout.flush()
else:
    print "\nGenerating final biotypes and GO terms table"
    sys.stdout.flush()
    name_id = pd.read_table(python_output+"/genes_table.txt", sep="\t")
    ontology = pd.read_table(python_output+"/biotypes_go_raw.txt")
    ontology.columns = ['g_id','gene_biotype','GO_id','GO_term']
    ontology = pd.merge(name_id, ontology, how='outer', on='g_id')
    ontology = ontology[['g_name','gene_biotype','GO_id','GO_term']]
    ontology.columns = ['gene_name','gene_biotype','GO_id','GO_term']

    final = pd.DataFrame(columns = ['gene_name','gene_biotype','GO_id','GO_term'])

    genes = ontology[['gene_name']]
    genes = genes.drop_duplicates()
    for gene in list(genes.gene_name):
        ontology_gene = ontology[ontology['gene_name'] == gene]
        ontology_gene_go = ontology_gene[['GO_id','GO_term']]
        if len(ontology_gene_go.index) >= 1:
            ontology_gene_go = ontology_gene_go.transpose()
            ontology_gene_go.to_csv("tmp.txt", sep=";", header=False, index=False)
            ontology_gene_go_number = pd.read_table("tmp.txt", sep ="\t", header=None, nrows = 1)
            ontology_gene_go_name = pd.read_table("tmp.txt", sep ="\t", header=None, skiprows=1, nrows = 1)
            ontology_gene_go = pd.concat([ontology_gene_go_number, ontology_gene_go_name], axis=1)
            ontology_gene_go.columns = ['GO_id','GO_term']
        else:
            ontology_gene_go = pd.DataFrame(columns = ['GO_id','GO_term'])
        
        ontology_gene = ontology_gene[['gene_name','gene_biotype']].drop_duplicates()
        ontology_gene_go = ontology_gene_go.reset_index()
        ontology_gene = ontology_gene.reset_index()
        ontology_gene = pd.concat([ontology_gene, ontology_gene_go], axis = 1)
        ontology_gene = ontology_gene[['gene_name','gene_biotype','GO_id','GO_term']]
        final = pd.concat([final, ontology_gene])
    os.remove("tmp.txt")
    final.reset_index()
    final=final[['gene_name','gene_biotype','GO_id','GO_term']]
    final.to_csv(python_output+"/biotypes_go.txt", sep= "\t")

    del name_id, ontology, genes, ontology_gene, ontology_gene_go, ontology_gene_go_number, ontology_gene_go_name, final


##################### Functions required for getting analysis from DAVID

def DAVIDenrich(listF, idType, bgF='', resF='', bgName = 'Background1',listName='List1', category = '', thd=0.1, ct=2):
    from suds.client import Client
    import os
   
    if len(listF) > 0 and os.path.exists(listF):
        inputListIds = ','.join(open(listF).read().split('\n'))
        print 'List loaded.'        
    else:
        print 'No list loaded.'
        raise

    flagBg = False
    if len(bgF) > 0 and os.path.exists(bgF):
        inputBgIds = ','.join(open(bgF).read().split('\n'))
        flagBg = True
        print 'Use file background.'
    else:
        print 'Use default background.'

    client = Client('http://david.abcc.ncifcrf.gov/webservice/services/DAVIDWebService?wsdl')
    print 'User Authentication:',client.service.authenticate(args.DAVIDuser)

    listType = 0
    print 'Percentage mapped(list):', client.service.addList(inputListIds,idType,listName,listType)
    if flagBg:
        listType = 1
        print 'Percentage mapped(background):', client.service.addList(inputBgIds,idType,bgName,listType)

    print 'Use categories:', client.service.setCategories(category)
    if float(client.service.addList(inputListIds,idType,listName,listType)) > float(0):
       
        chartReport = client.service.getChartReport(thd,ct)
        chartRow = len(chartReport)
        print 'Total chart records:',chartRow
    
        if len(resF) == 0 or not os.path.exists(resF):
            if flagBg:
                resF = listF + '.withBG.chartReport'
            else:
                resF = listF + '.chartReport'
        with open(resF, 'w') as fOut:
            fOut.write('Category\tTerm\tCount\t%\tPvalue\tGenes\tList Total\tPop Hits\tPop Total\tFold Enrichment\tBonferroni\tBenjamini\tFDR\n')
            for row in chartReport:
                rowDict = dict(row)
                categoryName = str(rowDict['categoryName'])
                termName = str(rowDict['termName'])
                listHits = str(rowDict['listHits'])
                percent = str(rowDict['percent'])
                ease = str(rowDict['ease'])
                Genes = str(rowDict['geneIds'])
                listTotals = str(rowDict['listTotals'])
                popHits = str(rowDict['popHits'])
                popTotals = str(rowDict['popTotals'])
                foldEnrichment = str(rowDict['foldEnrichment'])
                bonferroni = str(rowDict['bonferroni'])
                benjamini = str(rowDict['benjamini'])
                FDR = str(rowDict['afdr'])
                rowList = [categoryName,termName,listHits,percent,ease,Genes,listTotals,popHits,popTotals,foldEnrichment,bonferroni,benjamini,FDR]
                fOut.write('\t'.join(rowList)+'\n')
            print 'write file:', resF, 'finished!'
        
def DAVID_get(cat, filtered_table, all_genes_table):
    IDs_table = pd.merge(filtered_table, all_genes_table, how='left', left_on='identifier', right_on='g_name')
    IDs_table = IDs_table[['g_id']].dropna()
    IDs_table.to_csv('targets_tmp.txt',sep='\t',header=False,index=False)
        
    background = all_genes_table[['g_id']].dropna()
    background.to_csv('background_tmp.txt',sep='\t',header=False,index=False)
    
    DAVIDenrich(listF = './targets_tmp.txt', bgF = './background_tmp.txt', idType = DAVID_id, bgName = 'all_RNAseq_genes', listName = 'changed_genes', category = cat)
    if os.path.isfile('targets_tmp.txt.withBG.chartReport'):
        enrich=pd.read_csv('targets_tmp.txt.withBG.chartReport',sep='\t')
    	os.remove('targets_tmp.txt.withBG.chartReport')
        terms=enrich['Term'].tolist()
        enrichN=pd.DataFrame()
        for term in terms:
            tmp=enrich[enrich['Term']==term]
            tmp=tmp.reset_index(drop=True)
            ids=tmp.xs(0)['Genes']
            ids=pd.DataFrame(data=ids.split(", "))
            ids.columns=['g_id']
            ids['g_id']=ids['g_id'].map(str.lower)
            all_genes_table['g_id']=all_genes_table['g_id'].map(str.lower)
            ids=pd.merge(ids, all_genes_table, how='left', left_on='g_id', right_on='g_id')
            names=ids['g_name'].tolist()
            names = ', '.join(names)
            tmp=tmp.replace(to_replace=tmp.xs(0)['Genes'], value=names)
            enrichN=pd.concat([enrichN, tmp])
        enrichN=enrichN.reset_index(drop=True)

    else:
	enrichN=pd.DataFrame()
 
    os.remove('targets_tmp.txt')
    os.remove('background_tmp.txt')  
    
    return enrichN


# create excel report tables
print "\nCreating excel report tables"
sys.stdout.flush()

bio_go = pd.read_table(python_output+"/biotypes_go.txt", sep= "\t")

name_id = pd.read_table(python_output+"/genes_table.txt", sep="\t")

for sig, label in zip(sig_choice,label_choice):
    if sig != 'yes':
        writer = pd.ExcelWriter(python_output+'/'+label+'.xlsx')
        print "\nWritting table "+label+".xlsx"
        sys.stdout.flush()
    for imp, outshort in zip(in_files, out_labels):
	print "\nWorking on "+imp        
        sys.stdout.flush()

        if sig == 'yes':
            writer = pd.ExcelWriter(python_output+'/'+label+'_'+outshort+'.xlsx')
            print "Writting table "+label+"_"+outshort+".xlsx"            
            sys.stdout.flush()
            if args.DAVID:
		print "Starting DAVID's tables"
                bp_sheets=[]
		cc_sheets=[]
		mf_sheets=[]	
		
		writer_bp = pd.ExcelWriter(python_output+'/bio_process_'+label+'_'+outshort+'.xlsx')
                writer_cc = pd.ExcelWriter(python_output+'/cell_component_'+label+'_'+outshort+'.xlsx')
                writer_mf = pd.ExcelWriter(python_output+'/mol_function_'+label+'_'+outshort+'.xlsx')
                        
        df = pd.read_table(imp)
        df = df.sort('p_value')
        df = df.sort('q_value')
        if sig == 'yes':
            df = df[df['significant'] == 'yes']
        else:
            df = df[df['p_value'] < sig]
        df = df.reset_index()
        df['gene'] = df['gene'].astype(str)
        tmp = pd.DataFrame(df.gene.str.split(',',1).tolist())
        tmp = pd.DataFrame(tmp.ix[:,0])
        tmp.columns = ['identifier']
        df = pd.concat([df,tmp], axis=1)
        df = pd.merge(df, bio_go, how='left', left_on='identifier', right_on='gene_name')
                     
        if imp == 'isoform_exp.diff': # for isoform_exp.diff we want to have the transcript references
            gtf = pd.read_table(merged_fixed_gtf, sep='\t', skiprows=6, header=None)
            t_id = pd.DataFrame(gtf[8].str.split('transcript_id').tolist())[1]
            t_id = pd.DataFrame(t_id.str.split(';',1).tolist())
            t_id = pd.DataFrame(t_id[0].str.split('"').tolist())[1]
            
            n_ref = pd.DataFrame(gtf[8].str.split('nearest_ref').tolist())[1]
            n_ref = n_ref.astype(str)
            n_ref = pd.DataFrame(n_ref.str.split(';',1).tolist())
            n_ref = pd.DataFrame(n_ref[0].str.split('"').tolist())[1]
            
            id_ref = pd.concat([t_id, n_ref], axis=1).drop_duplicates()
            id_ref.columns = ['transcript_id','nearest_ref']
            
            df = pd.merge(id_ref, df, how='right', left_on='transcript_id', right_on='test_id')
              
        """for significant changes also report overlaps between the days, pair-wise, as well as go ontology enrichemnt for each table from DAVID"""
        if sig == 'yes': 
            	    	            
            def DAVID_write(table_of_interest, name_vs_id_table, sheet_name):
                if len(table_of_interest.index) >= 1:
                    enr = DAVID_get('GOTERM_BP_FAT,GOTERM_CC_FAT,GOTERM_MF_FAT', table_of_interest, name_vs_id_table)
                    if len(enr.index) >= 1:
                        if len(enr[enr['Category'] == 'GOTERM_BP_FAT']) > 0:
                            enr[enr['Category'] == 'GOTERM_BP_FAT'].to_excel(writer_bp, sheet_name, index=False)
		            bp_sheets.append(sheet_name)
                        if len(enr[enr['Category'] == 'GOTERM_CC_FAT']) > 0:    
			    enr[enr['Category'] == 'GOTERM_CC_FAT'].to_excel(writer_cc, sheet_name, index=False)
			    cc_sheets.append(sheet_name)
                        if len(enr[enr['Category'] == 'GOTERM_MF_FAT']) > 0:    
			    enr[enr['Category'] == 'GOTERM_MF_FAT'].to_excel(writer_mf, sheet_name, index=False)
            		    mf_sheets.append(sheet_name)	
				
            sample1 = df[['sample_1']]
            sample1.columns=['samples']
            sample2 = df[['sample_2']]
            sample2.columns=['samples']
            samples=pd.concat([sample1,sample2])
            samples=samples.drop_duplicates()
            samples=samples['samples'].tolist()

            for sample1 in samples:
                for sample2 in samples:
                    if sample1 != sample2:
                        if os.path.exists(sample1+sample2):
                            os.rmdir(sample1+sample2)
                        elif os.path.exists(sample2+sample1):
                            os.rmdir(sample2+sample1)

            for sample1 in samples:
                for sample2 in samples:
                    if sample1 != sample2:
                        if not os.path.exists(sample1+sample2): 
                            if not os.path.exists(sample2+sample1):

                                os.makedirs(sample1+sample2)
                                df_pair = df[df['sample_1'].isin([sample1,sample2])][df['sample_2'].isin([sample1,sample2])]
                                if args.DAVID:
                                    print "\nPerforming gene ontology enrichment analysis on "+sample1+' vs. '+sample2 
				    sys.stdout.flush()
                                    DAVID_write(df_pair, name_id, sample1+'|'+sample2)
            
                                df_pair.drop(['test_id','index','gene_id','Unnamed: 0','identifier','gene_name'], axis=1, inplace=True)
            
                                if imp not in ['gene_exp.diff','isoform_exp.diff']:
                                    df_pair.drop(['value_1','value_2','test_stat'], axis=1, inplace=True)
            
                                df_pair.to_excel(writer, sample1+'|'+sample2, index=False)
        
            for sample1 in samples:
                for sample2 in samples:
                    if sample1 != sample2:
                        if os.path.exists(sample1+sample2):
                            os.rmdir(sample1+sample2)
                        elif os.path.exists(sample2+sample1):
                            os.rmdir(sample2+sample1)
                            
        df.drop(['test_id','index','gene_id','Unnamed: 0','identifier','gene_name'], axis=1, inplace=True)
          
        if imp not in ['gene_exp.diff','isoform_exp.diff']:
            df.drop(['value_1','value_2','test_stat'], axis=1, inplace=True)
        
        if sig == 'yes':
            df.to_excel(writer, 'ALL', index=False)
                                       
                           
        if sig == 'yes':
            writer.save()
	    
	    if args.DAVID:

	        print "Closing DAVID's tables"
		if len(bp_sheets) == 0:
	            df_empty=pd.DataFrame()
		    df_empty.to_excel(writer_bp, "nothing_to_report", index=False)
		    writer_bp.save()
                    os.remove(python_output+'/bio_process_'+label+'_'+outshort+'.xlsx')
		else:
		    writer_bp.save()
 
		if len(cc_sheets) == 0:
		    df_empty=pd.DataFrame()
		    df_empty.to_excel(writer_cc, "nothing_to_report", index=False)
		    writer_cc.save()
  		    os.remove(python_output+'/cell_component_'+label+'_'+outshort+'.xlsx')
		else:
		    writer_cc.save() 

		if len(mf_sheets) == 0:
		    df_empty=pd.DataFrame()
		    df_empty.to_excel(writer_mf, "nothing_to_report", index=False)
		    writer_mf.save()
	            os.remove(python_output+'/mol_function_'+label+'_'+outshort+'.xlsx')
		else:
		    writer_mf.save()
                                       
    if sig != 'yes':
        df.to_excel(writer, outshort+'_'+'ALL', index=False)

                                       
print "\nDone"
print "\n\n*************************************\nDeveloped by Jorge Boucas at the group for Computational RNA Biology and Ageing of the Max Planck Institute for Biology of Ageing \n\njorge.boucas@age.mpg.de\n\n"
sys.exit()
