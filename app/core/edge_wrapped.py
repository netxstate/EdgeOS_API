import os
import uuid
from io import BytesIO
from typing import List, Optional, Set

from cairosvg import svg2png
from PIL import Image, ImageDraw, ImageFont

from app.core.logger import logger


def add_text_to_image(
    image_path: str,
    villages_count: int,
    days_count: int,
    events_count: int,
    output_path: str,
):
    """
    Adds metrics overlay to the input image
    """
    # Open the image
    img = Image.open(image_path).convert('RGBA')
    img_width, img_height = img.size

    # --- Define text properties (scale based on image width) ---
    # Base sizes for 1024px width
    base_width = 1024
    scale_factor = img_width / base_width

    font_size_label = int(32 * scale_factor)
    font_size_number = int(48 * scale_factor)
    try:
        font_label = ImageFont.truetype(
            'static/fonts/science-gothic.ttf', font_size_label
        )
        font_number = ImageFont.truetype(
            'static/fonts/science-gothic-bold.ttf', font_size_number
        )
    except IOError:
        logger.warning(
            'Warning: Science Gothic fonts not found, using default Pillow font.'
        )
        font_label = ImageFont.load_default()
        font_number = ImageFont.load_default()

    text_color = (255, 255, 255)  # White
    line_spacing = int(5 * scale_factor)

    # Set starting position from top (scaled)
    start_y = int(20 * scale_factor)  # Padding from the top

    # --- Draw the Text ---
    draw = ImageDraw.Draw(img)

    # Divide image into 3 equal columns
    column_width = img_width // 3

    # Get label height for positioning
    temp_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bbox_label = temp_draw.textbbox((0, 0), 'Villages attended', font=font_label)

    # Calculate consistent Y positions for all columns
    label_y = start_y
    number_y = start_y + (bbox_label[3] - bbox_label[1]) + line_spacing

    # LEFT COLUMN: Villages attended (centered in left third)
    label1 = 'Villages attended'
    number1 = str(villages_count)
    bbox_label1 = draw.textbbox((0, 0), label1, font=font_label)
    label1_width = bbox_label1[2] - bbox_label1[0]
    text_x_left = (column_width - label1_width) // 2
    draw.text((text_x_left, label_y), label1, font=font_label, fill=text_color)

    bbox_number1 = draw.textbbox((0, 0), number1, font=font_number)
    number1_width = bbox_number1[2] - bbox_number1[0]
    number_x_left = (column_width - number1_width) // 2
    draw.text((number_x_left, number_y), number1, font=font_number, fill=text_color)

    # CENTER COLUMN: Days at Edge (centered in middle third)
    label2 = 'Days at Edge'
    number2 = str(days_count)
    bbox_label2 = draw.textbbox((0, 0), label2, font=font_label)
    label2_width = bbox_label2[2] - bbox_label2[0]
    text_x_center = column_width + (column_width - label2_width) // 2
    draw.text((text_x_center, label_y), label2, font=font_label, fill=text_color)

    bbox_number2 = draw.textbbox((0, 0), number2, font=font_number)
    number2_width = bbox_number2[2] - bbox_number2[0]
    number_x_center = column_width + (column_width - number2_width) // 2
    draw.text((number_x_center, number_y), number2, font=font_number, fill=text_color)

    # RIGHT COLUMN: Events RSVP'd (centered in right third)
    label3 = "Events RSVP'd"
    number3 = str(events_count)
    bbox_label3 = draw.textbbox((0, 0), label3, font=font_label)
    label3_width = bbox_label3[2] - bbox_label3[0]
    text_x_right = (2 * column_width) + (column_width - label3_width) // 2
    draw.text((text_x_right, label_y), label3, font=font_label, fill=text_color)

    bbox_number3 = draw.textbbox((0, 0), number3, font=font_number)
    number3_width = bbox_number3[2] - bbox_number3[0]
    number_x_right = (2 * column_width) + (column_width - number3_width) // 2
    draw.text((number_x_right, number_y), number3, font=font_number, fill=text_color)

    # --- Add logo to bottom right corner ---
    try:
        # Convert SVG to PNG in memory (scaled)
        logo_height = int(80 * scale_factor)  # Desired height for the logo
        png_data = svg2png(url='static/images/edge-logo.svg', output_height=logo_height)
        logo = Image.open(BytesIO(png_data)).convert('RGBA')

        # Calculate position (bottom right with padding, scaled)
        logo_padding = int(20 * scale_factor)
        logo_x = img_width - logo.width - logo_padding
        logo_y = img_height - logo.height - logo_padding

        # Paste logo onto image
        img.paste(logo, (logo_x, logo_y), logo)
    except Exception as e:
        logger.warning('Could not add logo: %s', e)

    # --- Save ---
    img = img.convert('RGB')  # Convert back to RGB
    # Save as PNG with high quality to avoid compression artifacts
    img.save(output_path, format='PNG', optimize=False)
    logger.info('Image with text saved as %s', output_path)


def create_framed_image(
    center_image_path: str,
    background_path: str,
    popups: List[str],
    output_path: str,
):
    """
    Frames the center image with background and adds text at bottom
    """
    # Open the center image and convert to RGB
    center_img = Image.open(center_image_path).convert('RGB')
    center_width, center_height = center_img.size

    # Open the background/frame and use its dimensions
    background = Image.open(background_path).convert('RGB')
    canvas_width, canvas_height = background.size

    # Calculate scaling to fit the center image on background with padding
    padding = 150  # Desired padding from top and sides
    available_width = canvas_width - (padding * 2)
    available_height = (
        canvas_height - (padding * 2) - 200
    )  # Reserve space for text at bottom

    # Scale center image to fit
    scale = min(available_width / center_width, available_height / center_height)
    new_width = int(center_width * scale)
    new_height = int(center_height * scale)

    center_img_resized = center_img.resize((new_width, new_height))

    # Calculate position - center horizontally, then use same side padding for top
    x = (canvas_width - new_width) // 2  # Center horizontally
    actual_side_padding = x  # This is the actual padding on left/right
    y = actual_side_padding - 5  # Use padding for top, but reduce by 5 pixels

    # Paste center image onto background (no mask, since it's RGB)
    background.paste(center_img_resized, (x, y))

    # Add text at the bottom
    draw = ImageDraw.Draw(background)

    # Load fonts
    try:
        # Regular font
        title_font = ImageFont.truetype('static/fonts/science-gothic.ttf', 60)
        # Bold and bigger
        subtitle_font = ImageFont.truetype('static/fonts/science-gothic-bold.ttf', 70)
    except IOError:
        logger.warning('Science Gothic fonts not found, using default font.')
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    text_color = (21, 21, 21)  # Dark color

    # Text content
    title_text = 'YOUR EDGE WRAPPED, COMPROMISED OF:'
    # Convert popups list to comma-separated string
    subtitle_text = ', '.join(popups).upper()

    # Check if subtitle fits in one line
    bbox_subtitle_test = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width_test = bbox_subtitle_test[2] - bbox_subtitle_test[0]

    # Wrap subtitle if it doesn't fit (with some padding)
    available_text_width = canvas_width - 40  # 20px padding on each side
    subtitle_lines = []

    if subtitle_width_test > available_text_width:
        # Split into multiple lines
        words = subtitle_text.split(', ')
        current_line = words[0]

        for word in words[1:]:
            test_line = current_line + ', ' + word
            bbox_test = draw.textbbox((0, 0), test_line, font=subtitle_font)
            test_width = bbox_test[2] - bbox_test[0]

            if test_width <= available_text_width:
                current_line = test_line
            else:
                subtitle_lines.append(current_line + ',')
                current_line = word

        subtitle_lines.append(current_line)
    else:
        subtitle_lines = [subtitle_text]

    # Calculate dimensions
    bbox_title = draw.textbbox((0, 0), title_text, font=title_font)
    title_height = bbox_title[3] - bbox_title[1]

    bbox_subtitle_single = draw.textbbox((0, 0), subtitle_lines[0], font=subtitle_font)
    subtitle_line_height = bbox_subtitle_single[3] - bbox_subtitle_single[1]

    line_spacing = 10
    text_spacing = 20
    total_text_height = (
        title_height
        + text_spacing
        + (subtitle_line_height * len(subtitle_lines))
        + (line_spacing * (len(subtitle_lines) - 1))
    )

    # Calculate available space below image
    space_below_image = canvas_height - (y + new_height)

    # Center the text block vertically in the space below the image
    text_start_y = y + new_height + (space_below_image - total_text_height) // 2

    # Draw title
    title_width = bbox_title[2] - bbox_title[0]
    title_x = (canvas_width - title_width) // 2
    title_y = text_start_y
    draw.text((title_x, title_y), title_text, font=title_font, fill=text_color)

    # Draw subtitle lines
    current_y = title_y + title_height + text_spacing
    for line in subtitle_lines:
        bbox_line = draw.textbbox((0, 0), line, font=subtitle_font)
        line_width = bbox_line[2] - bbox_line[0]
        line_x = (canvas_width - line_width) // 2
        draw.text((line_x, current_y), line, font=subtitle_font, fill=text_color)
        current_y += subtitle_line_height + line_spacing

    # Save the result as PNG to avoid JPEG compression artifacts
    output_path_png = output_path.replace('.jpeg', '.png').replace('.jpg', '.png')
    background.save(output_path_png, format='PNG')
    logger.info('Framed image saved as %s', output_path_png)


def _generate_edge_wrapped(
    ai_image_path: str,
    villages_count: int,
    days_count: int,
    events_count: int,
    popups: List[str],
    background_frame_path='static/images/frame.png',
    intermediate_output: Optional[str] = None,
    final_output: Optional[str] = None,
):
    """
    Main function to generate both Edge Wrapped images

    Args:
        ai_image_path: Path to the AI-generated center image
        villages_count: Number of villages attended
        days_count: Number of days at Edge
        events_count: Number of events RSVP'd
        popups: List of popup/location names (e.g., ["Edge Austin", "Edge South Africa", "Edge Patagonia"])
        background_frame_path: Path to the background frame image (default: "frame.png")
        intermediate_output: Path to the intermediate image (default: None)
        final_output: Path to the final image (default: None)
    Returns:
        tuple: (intermediate_image_path, final_image_path)
    """
    image_id = str(uuid.uuid4())
    if not intermediate_output:
        intermediate_output = f'/tmp/{image_id}_intermediate.png'
    if not final_output:
        final_output = f'/tmp/{image_id}_final.png'

    # Step 1: Create image with metrics overlay
    logger.info('Step 1: Adding metrics overlay to image...')
    add_text_to_image(
        ai_image_path,
        villages_count,
        days_count,
        events_count,
        intermediate_output,
    )

    # Step 2: Create framed final image
    logger.info('Step 2: Creating framed final image...')
    create_framed_image(
        intermediate_output,
        background_frame_path,
        popups,
        final_output,
    )

    logger.info('\n✅ Generation complete!')
    logger.info('   - Intermediate image: %s', intermediate_output)
    logger.info('   - Final image: %s', final_output)

    return intermediate_output, final_output


def _get_ai_image(codes: Set[str]) -> str:
    directory = 'static/images'
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_file():
                filename = entry.name.split('.')[0]
                if codes == set(filename.split('-')):
                    return entry.path

    raise ValueError(f'No image found for codes: {codes}')


def generate_edge_wrapped(
    popups: List[str],
    days_count: int,
    events_count: int,
) -> str:
    popups_map = [
        # Name, Code
        ('Austin', 'AU'),
        ('South Africa', 'SA'),
        ('Patagonia', 'AR'),
        ('Lanna', 'TH'),
        ('Esmeralda', 'CA'),
        ('Bhutan', 'BH'),
    ]

    locations = set()
    codes = set()
    for popup in popups:
        for name, code in popups_map:
            if name.lower() in popup.lower():
                locations.add(name)
                codes.add(code)
                break

    villages_count = len(locations)
    ai_image_path = _get_ai_image(codes)

    intermediate_output, final_output = _generate_edge_wrapped(
        ai_image_path,
        villages_count,
        days_count,
        events_count,
        popups,
    )
    os.remove(intermediate_output)
    return final_output
