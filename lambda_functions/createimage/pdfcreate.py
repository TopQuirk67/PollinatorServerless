from weasyprint import HTML
import uuid
import os

def preprocess_html(html_content):
    return html_content

def create_pdf_from_html(html_content):
    # Save the processed HTML to a temporary file
    temp_html_path = f"/tmp/{uuid.uuid4()}.html"
    with open(temp_html_path, 'w') as file:
        file.write(html_content)

    # Debugging: Print the HTML content
    print("HTML content to be converted:")
    print(html_content)

    # Generate PDF from HTML using WeasyPrint
    pdf_path = f"/tmp/{uuid.uuid4()}.pdf"
    try:
        HTML(temp_html_path).write_pdf(pdf_path)
    except Exception as e:
        print(f"Error during PDF generation: {e}")
        with open('/tmp/weasyprint_error.log', 'w') as error_log:
            error_log.write(str(e))
        raise

    return pdf_path

if __name__ == '__main__':
    html_file_path = './output.html'  # Replace with your actual file path
    with open(html_file_path, 'r') as file:
        html_content = file.read()

    # Preprocess HTML (no changes in this case)
    html_content = preprocess_html(html_content)
    
    # Save the processed HTML to a file for debugging
    with open('/tmp/processed_output.html', 'w') as file:
        file.write(html_content)
    
    # Debugging: Print preprocessed HTML content
    print("Preprocessed HTML content saved to /tmp/processed_output.html")
    
    # Now you can use html_content in your functions
    pdf_path = create_pdf_from_html(html_content)
    print(f"PDF created at: {pdf_path}")