import pandas as pd
from spacy import displacy
from spacy.tokens import Doc
from spacy.vocab import Vocab
from spacy_streamlit.util import get_html
import streamlit as st
import torch
from transformers import BertTokenizerFast

from model import BertForTokenAndSequenceJointClassification


@st.cache(allow_output_mutation=True)
def load_model():
    tokenizer = BertTokenizerFast.from_pretrained('bert-base-cased')
    model = BertForTokenAndSequenceJointClassification.from_pretrained(
            "QCRI/PropagandaTechniquesAnalysis-en-BERT",
             revision="v0.1.0")
    return tokenizer, model

with torch.inference_mode(True):
    tokenizer, model = load_model()

    st.write("[Propaganda Techniques Analysis BERT](https://huggingface.co/QCRI/PropagandaTechniquesAnalysis-en-BERT) Tagger")

    input = st.text_area('Input', """\
    In some instances, it can be highly dangerous to use a medicine for the prevention or treatment of COVID-19 that has not been approved by or has not received emergency use authorization from the FDA.                         
    """)
    # input = st.text_area('Input', """\
    # WASHINGTON - President Donald Trump revealed an extraordinary plan for the United States to “take over” the Gaza Strip, resettle Palestinians in other countries – seemingly whether they wanted to leave or not – and turn the territory into “the Riviera of the Middle East”.He made the stunning proposal during a joint press conference with Israeli Prime Minister Benjamin Netanyahu, whom he was hosting at the White House for crucial talks on the truce with Hamas.In a scheme that lacked details on how he would move out more than two million Palestinians or control Gaza, Mr Trump said he would make the war-battered enclave “unbelievable” by removing unexploded bombs and rubble and economically redeveloping it.“The US will take over the Gaza Strip, and we will do a job with it, too. We’ll own it,” he said.Mr Trump said there was support from the “highest leadership” in the Middle East as he doubled down on his call for Palestinians to move out of the war-battered territory to Middle Eastern countries such as Egypt and Jordan, despite the Palestinians and both nations flatly rejecting his suggestion.Suggesting “long-term ownership” by the US, he said his plan for Gaza would make it “the Riviera of the Middle East. This could be something that could be so magnificent”.Key US ally Netanyahu said Mr Trump’s plan could “change history” and was worth “paying attention to”.Mr Netanyahu was making the first visit of a foreign leader to the White House since Mr Trump’s return to power, for what were billed as talks on securing a second phase of the Israel-Hamas truce after an initial six-week ceasefire.But it quickly turned into the shock revelation of a plan that would completely transform the face of the Middle East.
    # """)

    inputs = tokenizer.encode_plus(input, return_tensors="pt")
    outputs = model(**inputs)
    sequence_class_index = torch.argmax(outputs.sequence_logits, dim=-1)
    sequence_class = model.sequence_tags[sequence_class_index[0]]
    token_class_index = torch.argmax(outputs.token_logits, dim=-1)
    tokens = tokenizer.convert_ids_to_tokens(inputs.input_ids[0][1:-1])
    tags = [model.token_tags[i] for i in token_class_index[0].tolist()[1:-1]]

columns = st.columns(len(outputs.sequence_logits.flatten()))
for col, sequence_tag, logit in zip(columns, model.sequence_tags, outputs.sequence_logits.flatten()):
    col.metric(sequence_tag, '%.2f' % logit.item())


spaces = [not tok.startswith('##') for tok in tokens][1:] + [False]

doc = Doc(Vocab(strings=set(tokens)),
          words=tokens,
          spaces=spaces,
          ents=[tag if tag == "O" else f"B-{tag}" for tag in tags])

labels = model.token_tags[2:]

label_select = st.multiselect(
    "Tags",
    options=labels,
    default=labels,
    key=f"tags_ner_label_select",
)
html = displacy.render(
    doc, style="ent", options={"ents": label_select, "colors": {}}
)
style = "<style>mark.entity { display: inline-block }</style>"
st.write(f"{style}{get_html(html)}", unsafe_allow_html=True)

attrs = ["text", "label_", "start", "end", "start_char", "end_char"]
data = [
    [str(getattr(ent, attr)) for attr in attrs]
    for ent in doc.ents
    if ent.label_ in label_select
]
if data:
    df = pd.DataFrame(data, columns=attrs)
    st.dataframe(df)
