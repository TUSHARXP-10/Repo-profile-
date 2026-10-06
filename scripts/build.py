"""Regenerate every asset: ASCII portrait, typing SVG, info card, heatmap."""
import ascii_art
import ascii_svg
import contrib_card
import info_card
from common import load_config
from github_data import fetch


def main():
    ascii_art.main()
    ascii_svg.main()
    stats = fetch(load_config()["github_user"])
    info_card.main(stats)
    contrib_card.main(stats)


if __name__ == "__main__":
    main()
