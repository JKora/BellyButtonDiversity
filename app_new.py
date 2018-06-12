# Import dependencies
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import distinct

from flask import (Flask, render_template, jsonify, request, redirect)
import numpy as np
import pandas as pd

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Database Setup
#################################################

#Create engine for the bellybutton biodiversity table
engine = create_engine("sqlite:///belly_button_biodiversity.sqlite")

# reflect databases in ORM Classes
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect = True)
Base.classes.keys()

# save reference to tables in Bellybutton biodiversity database
Samples = Base.classes.samples
Metadata = Base.classes.samples_metadata
OTU = Base.classes.otu


#create  a database session object
session = Session(engine)

#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    samples_list = sample_names()
    return render_template('index.html', samples_list = samples_list)

@app.route("/names")
def sample_names():
    #list all of the samples
    sampleid_list = session.query(Metadata.SAMPLEID).all()
    
    #Convert list if tuples into normal list
    sample_list = list(np.ravel(sampleid_list))

    #convert the sample_id list into required format
    pretty_samples = []
    for sample in sample_list:
        pretty_samples.append("BB_"+str(sample))
        
    return jsonify(pretty_samples)

@app.route("/otu")
def otu_descriptions():
    #list of all unique otu descriptions
    otu_descs = session.query(distinct(OTU.lowest_taxonomic_unit_found)).all()
    
    #convert list of tuples into normal list
    otu_descs = list(np.ravel(otu_descs))
    
    return jsonify(otu_descs)

@app.route("/metadata/<sample>")
def sample_metadata(sample):
    query_sample = int(sample[3:])
    sample_meta = {}
    for metadata in session.query(Metadata).filter(Metadata.SAMPLEID==query_sample).all():
        sample_meta = (metadata.__dict__)
    if(len(sample_meta) == 0):
        result = f'Sample Metadata not available for {sample}'
    else :
        sample_keys = ["AGE", "BBTYPE", "ETHNICITY", "GENDER", "LOCATION", "SAMPLEID"]
        result = {key:sample_meta[key] for key in sample_keys}
    
    return jsonify(result)

@app.route("/wfreq/<sample>")
def wash_freq(sample):
    query_sample = int(sample[3:])
    wfreq = session.query(Metadata.WFREQ).filter(Metadata.SAMPLEID == query_sample).all()
    result = f'The wash frequency for sample {sample} is {wfreq[0][0]}'
    
    return result

@app.route("/samples/<sample>")
def sample_otu(sample):
    samples_df = pd.read_sql_table('samples', engine)
    result_df = ((samples_df[samples_df[sample]>0]).sort_values(by = sample, ascending=False))[['otu_id', sample]]
    result_df.columns = ['otu_id', 'sample_values']
    sample_otu_result = result_df.to_dict(orient='list')
    
    return jsonify(sample_otu_result)

if __name__ == "__main__":
    app.run(debug=True)


