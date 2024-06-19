import time

import streamlit as st
import uuid
from utils import *
import json

if 'unique_id' not in st.session_state:
    st.session_state['unique_id'] = ''

if 'generated_jd' not in st.session_state:
    st.session_state['generated_jd'] = ""


def main():
    st.set_page_config(page_title="HR | Match Maker")
    logo_url = "https://createch.solutions/wp-content/uploads/2017/05/IBA.png"  # Replace with the actual URL of your logo

    col1, col2, col3 = st.columns([2, 2, 2])
    # Display the logo using st.image
    with col2:
        st.image(logo_url, width=200)

    st.title("HR | Match Maker")
    # st.subheader("Let me help you analyze the Resumes....")

    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        years_of_experience = st.selectbox(
            'Years of Experience',
            ('Fresh', '0-1', '1', '2', '3', '4', '5', '5+'),
            key=1
        )

    with col2:
        domain = st.selectbox(
            'Domain',
            ('Programming', 'Human Resource', 'Support Staff'),
            key=2
        )

    with col3:
        sub_domain_choices = {
            'Programming': ['Python', 'Java', 'PHP', 'C++', '.Net'],
            'Human Resource': ['Talent Acquisition', 'Business Partners', 'Operations'],
            'Support Staff': ['IT Support', 'Network Support']
        }

        sub_domain = st.selectbox('Sub Domain', options=sub_domain_choices[domain], key=3)

    addition_skills = st.text_area("Please add additional skills you want in the candidate", key=5,
                                   placeholder="Please add any "
                                               "other skills "
                                               "you want in the "
                                               "candidate",
                                   height=300)

    jd_requiremnts = {
        "years_of_exp": years_of_experience,
        "domain": domain,
        "sub_domain": sub_domain,
        "other_skills": addition_skills
    }

    def generate_jd_btn_clicked():
        st.session_state['generated_jd'] = generate_job_description(jd_requiremnts)

    st.button("Generate Job Description", on_click=generate_jd_btn_clicked)

    job_description = st.text_area("Please add job description here", value=st.session_state['generated_jd'], key=6,
                                   placeholder="Job Description", height=600)
    document_count = st.text_input("How many resumes you want to match", key=7)

    pdf = st.file_uploader("Upload resumes here, Only PDF files allowed", type=["pdf"], accept_multiple_files=True)

    submit = st.button("Analyze")
    st.write("This is the best candidate")
    if submit:
        with st.spinner("Wait for it...."):
            st.session_state['unique_id'] = uuid.uuid4().hex

            final_docs_list = create_docs(pdf, st.session_state['unique_id'])

            st.write("Resumes Uploaded:" + str(len(final_docs_list)))

            embeddings = create_embeddings()

            create_chroma_db(embeddings, final_docs_list)

            relevant_docs = similar_docs(job_description, document_count, embeddings, st.session_state['unique_id'])
            # print(relevant_docs)
            st.write(":heavy_minus_sign:" * 30)

            for item in range(len(relevant_docs)):
                st.subheader("Item:" + str(item + 1))
                st.write("Currently Analyzing File :" + relevant_docs[item][0].metadata['name'])

                with st.expander("Show details"):
                    # st.info("**Good Match** :" + str(1 - relevant_docs[item][1]))
                    resume_summary = get_summary_of_resume(relevant_docs[item][0])
                    time.sleep(2)

                    summary = generate_resume_reasoning(resume=relevant_docs[item][0], job_description=job_description)
                    # print(summary)
                    # print(summary)
                    print(type(summary))
                    # st.write("Resume Evaluation:" + summary)
                    # # summary = json.loads(summary)
                    if summary['evaluation']:
                        evaluation = summary['evaluation']
                    if summary['strengths']:
                        strengths = summary['strengths']
                    if summary['weakness']:
                        weakness = summary['weakness']
                    # verdict = summary['verdict']
                    rating = summary['rating']
                    verdict = ""

                    if rating >= 7:
                        st.success("**Good Match** Rating according to JD: " + str(rating) + "/10")
                        verdict = "This Candidate is highly aligned with the job requirements."
                    elif 7 > rating >= 4:
                        st.warning("**Medium Match** Rating according to JD: " + str(rating) + "/10")
                        verdict = "This Candidate is moderately aligned with the job requirements."
                    else:
                        st.error("**Not a Good Match** Rating according to JD: " + str(rating) + "/10")
                        verdict = "This Candidate is not aligned with the job requirements."

                    if resume_summary:
                        st.write("Summary of Resume:" + str(resume_summary))

                    if evaluation:
                        st.write("Resume Evaluation:" + str(evaluation))
                    if strengths:
                        st.write("Candidate Strengths:" + str(strengths))
                    if weakness:
                        st.write("Candidate Weakness:" + str(weakness))
                    if verdict:
                        st.write("Should We Hire? :" + str(verdict))

        st.success("Resume Analysis has been completed.")


if __name__ == "__main__":
    main()
