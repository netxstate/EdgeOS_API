import os
from io import BytesIO
from typing import List, Optional, Set
from uuid import uuid4

from cairosvg import svg2png
from fastapi import HTTPException, status
from PIL import Image, ImageDraw, ImageFont

from app.core.logger import logger


def add_text_to_image(
    image_path, villages_count, days_count, events_count, output_path
):
    """
    Adds metrics overlay to the input image, styled like the example.
    """
    # Open the image
    img = Image.open(image_path).convert('RGBA')
    img_width, img_height = img.size
    draw = ImageDraw.Draw(img)

    # --- Define text properties (scale based on image width) ---
    base_width = 1024  # Based on the example image size
    scale_factor = img_width / base_width

    # Greatly increased number size, smaller label size
    font_size_number = int(120 * scale_factor)
    font_size_label = int(30 * scale_factor)

    try:
        font_number = ImageFont.truetype(
            'static/fonts/PPRightGroteskMono-Regular.otf', font_size_number
        )
        font_label = ImageFont.truetype(
            'static/fonts/PPRightGroteskMono-Regular.otf', font_size_label
        )
    except IOError:
        logger.warning('PP Right Grotesk Mono fonts not found')
        font_number = ImageFont.load_default()
        font_label = ImageFont.load_default()

    text_color = (0, 0, 0)  # Black text
    # Space between number and label block
    h_spacing = int(20 * scale_factor)
    # Space between the two lines of the label
    v_spacing = int(5 * scale_factor)

    # --- Data for the three columns ---
    stats = [
        {'label': 'Villages\nAttended', 'count': villages_count},
        {'label': 'Days\nat Edge', 'count': days_count},
        {'label': 'Events\nRSVPed', 'count': events_count},
    ]

    # --- Draw each stat block ---
    column_width = img_width // 3
    start_y = int(20 * scale_factor)  # Padding from the top

    for i, stat in enumerate(stats):
        number_str = str(stat['count'])
        label_str = stat['label']

        # --- Calculate dimensions ---
        # Bbox for the large number
        bbox_number = draw.textbbox((0, 0), number_str, font=font_number)
        number_width = bbox_number[2] - bbox_number[0]
        number_bbox_top = bbox_number[1]

        # Bbox for the two-line label
        bbox_label = draw.textbbox(
            (0, 0), label_str, font=font_label, spacing=v_spacing
        )
        label_width = bbox_label[2] - bbox_label[0]
        label_bbox_top = bbox_label[1]

        # Total width of the stat block (number + spacing + label)
        total_block_width = number_width + h_spacing + label_width

        # --- Calculate positions ---
        # Adjust block_start_x based on the column for alignment
        column_padding = int(40 * scale_factor)

        if i == 0:  # Left column: align left
            block_start_x = (i * column_width) + column_padding
        elif i == 2:  # Right column: align right
            block_start_x = (
                ((i + 1) * column_width) - total_block_width - column_padding
            )
        else:  # Center column: align center
            block_start_x = (i * column_width) + (column_width - total_block_width) // 2

        # --- Y Position Calculation (The Fix) ---
        # Align the top of the label to start_y
        label_y = start_y
        # Calculate number_y to align the top of the number's bounding box with the label's
        number_y = start_y + label_bbox_top - number_bbox_top

        # X positions for number and label
        number_x = block_start_x
        label_x = block_start_x + number_width + h_spacing

        # --- Draw the text ---
        # Draw the large number
        draw.text((number_x, number_y), number_str, font=font_number, fill=text_color)

        # Draw the two-line label
        draw.text(
            (label_x, label_y),
            label_str,
            font=font_label,
            fill=text_color,
            spacing=v_spacing,
        )

    # --- Add logo to bottom right corner ---
    try:
        # Convert SVG to PNG in memory (scaled)
        logo_height = int(80 * scale_factor)  # Desired height for the logo
        png_data = svg2png(url='static/images/edge-logo.svg', output_height=logo_height)
        logo = Image.open(BytesIO(png_data)).convert('RGBA')

        # Calculate position (bottom right with padding, scaled)
        logo_padding = int(40 * scale_factor)
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


def create_framed_image(center_image_path, background_path, popups, output_path):
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
    padding = 80  # Desired padding from top and sides
    available_width = canvas_width - (padding * 2)
    available_height = (
        canvas_height - (padding * 2) - 200
    )  # Reserve space for text at bottom

    # Scale center image to fit
    scale = min(available_width / center_width, available_height / center_height)
    new_width = int(center_width * scale)
    new_height = int(center_height * scale)

    center_img_resized = center_img.resize((new_width, new_height))

    # Add 1px black frame to the resized center image
    frame_draw = ImageDraw.Draw(center_img_resized)
    frame_width = 2
    frame_draw.rectangle(
        (0, 0, new_width - frame_width, new_height - frame_width),
        outline=(0, 0, 0),
        width=frame_width,
    )

    # Calculate position - center horizontally, then use same side padding for top
    x = (canvas_width - new_width) // 2  # Center horizontally
    actual_side_padding = x  # This is the actual padding on left/right
    y = actual_side_padding - 5  # Use padding for top, but reduce by 5 pixels

    # Paste center image onto background (no mask, since it's RGB)
    background.paste(center_img_resized, (x, y))

    # --- Draw L-shaped corners (inwards) ---
    draw = ImageDraw.Draw(background)
    corner_offset = 15
    corner_length = 30
    corner_color = (0, 0, 0)
    corner_width = 2

    # Top-left corner
    draw.line(
        (
            x - corner_offset,
            y - corner_offset,
            x - corner_offset + corner_length,
            y - corner_offset,
        ),
        fill=corner_color,
        width=corner_width,
    )
    draw.line(
        (
            x - corner_offset,
            y - corner_offset,
            x - corner_offset,
            y - corner_offset + corner_length,
        ),
        fill=corner_color,
        width=corner_width,
    )

    # Top-right corner
    draw.line(
        (
            x + new_width + corner_offset,
            y - corner_offset,
            x + new_width + corner_offset - corner_length,
            y - corner_offset,
        ),
        fill=corner_color,
        width=corner_width,
    )
    draw.line(
        (
            x + new_width + corner_offset,
            y - corner_offset,
            x + new_width + corner_offset,
            y - corner_offset + corner_length,
        ),
        fill=corner_color,
        width=corner_width,
    )

    # Bottom-left corner
    draw.line(
        (
            x - corner_offset,
            y + new_height + corner_offset,
            x - corner_offset + corner_length,
            y + new_height + corner_offset,
        ),
        fill=corner_color,
        width=corner_width,
    )
    draw.line(
        (
            x - corner_offset,
            y + new_height + corner_offset,
            x - corner_offset,
            y + new_height + corner_offset - corner_length,
        ),
        fill=corner_color,
        width=corner_width,
    )

    # Bottom-right corner
    draw.line(
        (
            x + new_width + corner_offset,
            y + new_height + corner_offset,
            x + new_width + corner_offset - corner_length,
            y + new_height + corner_offset,
        ),
        fill=corner_color,
        width=corner_width,
    )
    draw.line(
        (
            x + new_width + corner_offset,
            y + new_height + corner_offset,
            x + new_width + corner_offset,
            y + new_height + corner_offset - corner_length,
        ),
        fill=corner_color,
        width=corner_width,
    )

    # Add text at the bottom
    draw = ImageDraw.Draw(background)

    # Load fonts
    try:
        # Main title font - PP Editorial Old Italic
        title_font = ImageFont.truetype('static/fonts/PPEditorialOld-Italic.otf', 100)
        # Subtitle font - PP Right Grotesk Mono Regular Italic
        subtitle_font = ImageFont.truetype(
            'static/fonts/PPRightGroteskMono-RegularItalic.otf', 29
        )
        # Villages font - PP Right Grotesk Mono Medium
        villages_font = ImageFont.truetype(
            'static/fonts/PPRightGroteskMono-Medium.otf', 40
        )
    except IOError:
        logger.warning('Required fonts not found, trying alternatives...')
        try:
            # Fallback to regular italic if specific italic version not found
            title_font = ImageFont.truetype(
                'static/fonts/PPEditorialOld-Italic.otf', 100
            )
            subtitle_font = ImageFont.truetype(
                'static/fonts/PPRightGroteskMono-Regular.otf', 29
            )
            villages_font = ImageFont.truetype(
                'static/fonts/PPRightGroteskMono-Medium.otf', 40
            )
        except IOError:
            logger.warning('Fonts not found, using defaults.')
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            villages_font = ImageFont.load_default()

    title_color = (0, 0, 0)  # Black for title and villages
    subtitle_color = (84, 84, 84)  # #545454 for subtitle

    # Text content
    title_text = 'Edge Mapped'
    subtitle_text = 'Comprised of your villages:'
    # Convert popups list to comma-separated string (no uppercasing)
    villages_text = ', '.join(popups)

    # Check if villages text fits in one line
    bbox_villages_test = draw.textbbox((0, 0), villages_text, font=villages_font)
    villages_width_test = bbox_villages_test[2] - bbox_villages_test[0]

    # Wrap villages if they don't fit (with some padding)
    available_text_width = canvas_width - 40  # 20px padding on each side
    villages_lines = []

    if villages_width_test > available_text_width:
        # Split into multiple lines
        words = villages_text.split(', ')
        current_line = words[0]

        for word in words[1:]:
            test_line = current_line + ', ' + word
            bbox_test = draw.textbbox((0, 0), test_line, font=villages_font)
            test_width = bbox_test[2] - bbox_test[0]

            if test_width <= available_text_width:
                current_line = test_line
            else:
                villages_lines.append(current_line)
                current_line = word

        villages_lines.append(current_line)
    else:
        villages_lines = [villages_text]

    # Calculate dimensions
    bbox_title = draw.textbbox((0, 0), title_text, font=title_font)
    title_height = bbox_title[3] - bbox_title[1]

    bbox_subtitle = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_height = bbox_subtitle[3] - bbox_subtitle[1]

    bbox_villages_single = draw.textbbox((0, 0), villages_lines[0], font=villages_font)
    villages_line_height = bbox_villages_single[3] - bbox_villages_single[1]

    line_spacing = 5
    text_spacing = 15
    total_text_height = (
        title_height
        + text_spacing
        + subtitle_height
        + text_spacing
        + (villages_line_height * len(villages_lines))
        + (line_spacing * (len(villages_lines) - 1))
    )

    # Calculate available space below image
    space_below_image = canvas_height - (y + new_height)

    # Center the text block vertically in the space below the image
    text_start_y = y + new_height + (space_below_image - total_text_height) // 2

    # Draw title
    title_width = bbox_title[2] - bbox_title[0]
    title_x = (canvas_width - title_width) // 2
    title_y = text_start_y
    draw.text((title_x, title_y), title_text, font=title_font, fill=title_color)

    # Draw subtitle
    subtitle_width = bbox_subtitle[2] - bbox_subtitle[0]
    subtitle_x = (canvas_width - subtitle_width) // 2
    subtitle_y = title_y + title_height + text_spacing
    draw.text(
        (subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=subtitle_color
    )

    # Draw villages lines
    current_y = subtitle_y + subtitle_height + text_spacing
    for line in villages_lines:
        bbox_line = draw.textbbox((0, 0), line, font=villages_font)
        line_width = bbox_line[2] - bbox_line[0]
        line_x = (canvas_width - line_width) // 2
        draw.text((line_x, current_y), line, font=villages_font, fill=title_color)
        current_y += villages_line_height + line_spacing

    # Save the result as PNG to avoid JPEG compression artifacts
    output_path_png = output_path.replace('.jpeg', '.png').replace('.jpg', '.png')
    background.save(output_path_png, format='PNG')
    logger.info('Framed image saved as %s', output_path_png)


def _generate_edge_mapped(
    ai_image_path: str,
    villages_count: int,
    days_count: int,
    events_count: int,
    popups: List[str],
    background_path='static/images/background.png',
    intermediate_output: Optional[str] = None,
    final_output: Optional[str] = None,
):
    """
    Main function to generate both Edge Mapped images

    Args:
        ai_image_path: Path to the AI-generated center image
        villages_count: Number of villages attended
        days_count: Number of days at Edge
        events_count: Number of events RSVP'd
        popups: List of popup/location names (e.g., ["Edge Austin", "Edge South Africa", "Edge Patagonia"])
        background_path: Path to the background image (default: "background.png")

    Returns:
        tuple: (intermediate_image_path, final_image_path)
    """
    image_id = str(uuid4())
    if not intermediate_output:
        intermediate_output = f'/tmp/{image_id}_intermediate.png'
    if not final_output:
        final_output = f'/tmp/{image_id}_final.png'

    # Step 1: Create image with metrics overlay
    logger.info('Step 1: Adding metrics overlay to image...')
    add_text_to_image(
        ai_image_path, villages_count, days_count, events_count, intermediate_output
    )

    # Step 2: Create framed final image
    logger.info('Step 2: Creating framed final image...')
    create_framed_image(intermediate_output, background_path, popups, final_output)

    logger.info('Generation complete!')
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


def generate_edge_mapped(
    popups: List[str],
    days_count: int,
    events_count: int,
) -> str:
    popups_map = [
        # Name, Code
        ('Esmeralda 2024', 'CA'),
        ('Lanna', 'TH'),
        ('Austin', 'AU'),
        ('South Africa', 'SA'),
        ('Esmeralda 2025', 'CA'),
        ('Bhutan', 'BH'),
        ('Patagonia', 'AR'),
    ]

    locations = []
    codes = []
    for name, code in popups_map:
        for popup in popups:
            if name.lower() in popup.lower():
                if name not in locations:
                    locations.append(name)
                if code not in codes:
                    codes.append(code)

    if not codes or not locations:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            'No edge mapped available',
        )
    villages_count = len(locations)
    ai_image_path = _get_ai_image(codes)

    if 'Austin' in locations:
        events_count += 8
    if 'South Africa' in locations:
        events_count += 12
    if 'Bhutan' in locations:
        events_count += 10

    intermediate_output, final_output = _generate_edge_mapped(
        ai_image_path,
        villages_count,
        days_count,
        events_count,
        locations,
    )
    os.remove(intermediate_output)
    return final_output
