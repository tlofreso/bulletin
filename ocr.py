
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, ContentFormat


KEY       = os.environ["AZURE_KEY"]
ENDPOINT  = os.environ["AZURE_ENDPOINT"]
CLIENT    = DocumentIntelligenceClient(ENDPOINT, AzureKeyCredential(KEY))

def analyze_document(f):
    poller = CLIENT.begin_analyze_document("prebuilt-layout", AnalyzeDocumentRequest(bytes_source=f.read()), output_content_format=ContentFormat.MARKDOWN)
    result = poller.result().as_dict()
    return result
