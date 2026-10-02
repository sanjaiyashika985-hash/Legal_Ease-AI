import os
import tempfile
from pathlib import Path

import requests
import streamlit as st

from dotenv import load_dotenv

from backend.utils.exporters import (
    make_export
)

from backend.utils.text_utils import (
    text_to_html
)


load_dotenv()


BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(

    page_title="LegalEase",

    page_icon="⚖️",

    layout="wide",

    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>

    .hero {

        padding: 1.5rem;

        border-radius: 18px;

        background:
            linear-gradient(
                135deg,
                #111827,
                #1f2937
            );

        color: white;

        margin-bottom: 1.5rem;
    }


    .hero h1 {

        margin: 0;

        font-size: 2.5rem;
    }


    .hero p {

        margin-top: 0.5rem;

        color: #d1d5db;
    }


    .preview {

        background: #111827;

        color: #f9fafb;

        border-radius: 14px;

        padding: 1.5rem;

        max-height: 650px;

        overflow-y: auto;

        line-height: 1.7;
    }


    .preview h3 {

        color: #93c5fd;

        margin-top: 1rem;
    }


    .preview .clause {

        margin-left: 0.5rem;
    }


    .spacer {

        height: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "document" not in st.session_state:

    st.session_state.document = ""


if "doc_type" not in st.session_state:

    st.session_state.doc_type = (
        "Non-Disclosure Agreement"
    )


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.html(
    """
    <div class="hero">

        <h1>⚖️ LegalEase</h1>

        <p>
            AI-powered legal document
            drafting, editing and export.
        </p>

    </div>
    """
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header(
        "⚖️ LegalEase"
    )


    document_type = st.selectbox(

        "Document Type",

        [

            "Employment Contract",

            "Non-Disclosure Agreement",

            "Lease Agreement",

            "Employment Offer Letter",

            "Freelance Work Contract",

            "Service Agreement",

            "Partnership Agreement",

            "Custom Legal Agreement"

        ]
    )


    language = st.selectbox(

        "Language",

        [

            "English",

            "Tamil",

            "Hindi",

            "Malayalam",

            "Telugu"

        ]
    )


    jurisdiction = st.text_input(

        "Jurisdiction",

        value="Not specified"

    )


    logo = st.file_uploader(

        "Upload Company Logo",

        type=[
            "png",
            "jpg",
            "jpeg"
        ]
    )


    st.divider()


    st.caption(

        "LegalEase creates drafts. "
        "Review important documents "
        "with a qualified legal professional."
    )


# --------------------------------------------------
# INPUT / PREVIEW
# --------------------------------------------------

left_column, right_column = st.columns(
    [1, 1]
)


# --------------------------------------------------
# INPUT SECTION
# --------------------------------------------------

with left_column:

    st.subheader(
        "Document Inputs"
    )


    parties = st.text_area(

        "Parties Involved",

        placeholder=(
            "Jane Doe (Service Provider), "
            "TechNova Inc. (Client)"
        ),

        height=110
    )


    terms = st.text_area(

        "Terms & Conditions",

        placeholder=(
            "Payment within 30 days; "
            "Confidentiality must be maintained; "
            "Either party may terminate with 15 days notice"
        ),

        height=180,

        help=(
            "Separate major terms using semicolons (;)"
        )
    )


    effective_date = st.text_input(

        "Effective Date",

        placeholder=(
            "September 30, 2026"
        )
    )


    additional_instructions = st.text_area(

        "Additional Instructions",

        placeholder=(
            "Add any special clauses "
            "or formatting requirements."
        ),

        height=100
    )


    generate_button = st.button(

        "✨ Generate Document",

        type="primary",

        use_container_width=True
    )


# --------------------------------------------------
# GENERATE
# --------------------------------------------------

if generate_button:

    if not parties.strip():

        st.error(
            "Please enter the parties involved."
        )

    elif not terms.strip():

        st.error(
            "Please enter the terms."
        )

    elif not effective_date.strip():

        st.error(
            "Please enter the effective date."
        )

    else:

        payload = {

            "document_type":
                document_type,

            "parties":
                parties,

            "terms":
                terms,

            "effective_date":
                effective_date,

            "jurisdiction":
                jurisdiction,

            "additional_instructions":
                additional_instructions,

            "language":
                language
        }


        try:

            with st.spinner(
                "Generating your legal document..."
            ):

                response = requests.post(

                    f"{BACKEND_URL}/generate",

                    json=payload,

                    timeout=180
                )


            if response.ok:

                data = response.json()


                st.session_state.document = (
                    data["content"]
                )


                st.session_state.doc_type = (
                    document_type
                )


                if data["mock_mode"]:

                    st.info(

                        "Gemini API key is not "
                        "configured. Running in "
                        "local mock mode."
                    )

                else:

                    st.success(

                        f"Generated using "
                        f"{data['model']}"
                    )


            else:

                try:

                    detail = (
                        response
                        .json()
                        .get(
                            "detail",
                            response.text
                        )
                    )

                except Exception:

                    detail = response.text


                st.error(
                    f"Backend Error: {detail}"
                )


        except requests.RequestException as error:

            st.error(

                "Cannot connect to FastAPI."
            )

            st.info(

                "Start the backend using:\n\n"
                "uvicorn backend.main:app --reload"
            )

            st.caption(
                str(error)
            )


# --------------------------------------------------
# PREVIEW
# --------------------------------------------------

with right_column:

    st.subheader(
        "Document Preview"
    )


    if st.session_state.document:

        html_preview = text_to_html(

            st.session_state.document
        )


        st.html(

            f"""
            <div class="preview">

                {html_preview}

            </div>
            """
        )

    else:

        st.info(

            "Your generated document "
            "will appear here."
        )


# --------------------------------------------------
# EDITOR
# --------------------------------------------------

if st.session_state.document:

    st.divider()

    st.subheader(
        "Edit Document"
    )


    edited_document = st.text_area(

        "Editable Document",

        value=st.session_state.document,

        height=500,

        label_visibility="collapsed"
    )


    st.session_state.document = (
        edited_document
    )


    # --------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------

    st.subheader(
        "Download Document"
    )


    col1, col2, col3 = st.columns(3)


    logo_path = None

    temporary_logo = None


    if logo:

        temporary_logo = (
            tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(
                    logo.name
                ).suffix.lower()
            )
        )


        temporary_logo.write(
            logo.getvalue()
        )


        temporary_logo.close()


        logo_path = (
            temporary_logo.name
        )


    try:

        # TXT

        txt_data, txt_mime, txt_filename = (
            make_export(

                st.session_state.document,

                st.session_state.doc_type,

                "txt",

                logo_path
            )
        )


        col1.download_button(

            "⬇️ Download TXT",

            data=txt_data,

            file_name=txt_filename,

            mime=txt_mime,

            use_container_width=True
        )


        # DOCX

        docx_data, docx_mime, docx_filename = (
            make_export(

                st.session_state.document,

                st.session_state.doc_type,

                "docx",

                logo_path
            )
        )


        col2.download_button(

            "⬇️ Download DOCX",

            data=docx_data,

            file_name=docx_filename,

            mime=docx_mime,

            use_container_width=True
        )


        # PDF

        pdf_data, pdf_mime, pdf_filename = (
            make_export(

                st.session_state.document,

                st.session_state.doc_type,

                "pdf",

                logo_path
            )
        )


        col3.download_button(

            "⬇️ Download PDF",

            data=pdf_data,

            file_name=pdf_filename,

            mime=pdf_mime,

            use_container_width=True
        )


    finally:

        if temporary_logo:

            try:

                os.unlink(
                    temporary_logo.name
                )

            except OSError:

                pass


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.caption(

    "LegalEase — AI-assisted drafting tool. "
    "Verify legal and jurisdiction-specific "
    "requirements before signing."
)