import requests
from PIL import Image
from io import BytesIO


def fetch_and_save_image(url, headers, file_name):
    try:
        # Send a request to fetch the binary image data
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Convert the response content into a PIL image
            image_data = BytesIO(response.content)
            image = Image.open(image_data)

            # Save the image to a file
            image.save(file_name)
            print(f"Image saved as {file_name}")
        else:
            print(f"Failed to fetch the image. Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage
url = "https://example.com/image.png"  # Replace this with your image URL
headers = {
    'x-rapidapi-key': "YOUR_API_KEY",
    'x-rapidapi-host': "YOUR_API_HOST"
}
file_name = "league_image.png"  # Specify the file name to save the image

fetch_and_save_image(url, headers, file_name)