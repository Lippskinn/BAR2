import datetime
import logging
import os
import random

from django.contrib.auth.models import User
from django.core.files import File
from django.utils import timezone

from accounts.models import Borrower, Lender
from core.settings import BASE_DIR
from respool.models import Category, Item, Dimension, Location, Loan, LoanAgreement, RentalFee, Image, TimeInterval

'''Script for populating the respool with dummy items'''
'''Author: Marius Hofmann'''

logger = logging.getLogger(__name__)


def create():
    """Main function, called from command.
    Calls subroutines for populating the database."""
    create_locations()
    create_users()
    create_categories()
    create_items()
    add_occupancies_to_items()


def create_users():
    logger.debug("creating Borrowers")
    create_borrower("Hans", "Georg", "HaGe")
    create_borrower("Dirk", "Herman", "DerMan")
    create_borrower("Torsten", "Fiedler", "TorF")
    create_borrower("Matthias", "Bayer", "MatthiB")
    logger.debug("done creating Borrowers")

    logger.debug("creating Lenders")
    create_lender("Sebastian", "Baumgartner", "SebBaum")
    create_lender("Maik", "Kohler", "MaikK")
    create_lender("Markus", "Nagel", "Markel")
    create_lender("Ines", "Fischer", "FInes")
    create_lender("Manuela", "Schuhmacher", "Schuela")
    create_lender("Andrea", "Shuster", "Shandrea")
    create_lender("Birgit", "Kaestner", "Birne")
    create_lender("Petra", "Bayer", "PetBa")
    logger.debug("done creating Lenders")


def create_borrower(first_name, last_name, user_name):
    user, _ = User.objects.get_or_create(first_name=first_name, last_name=last_name, username=user_name,
                                         email='{}@{}.de'.format(first_name.lower(), last_name.lower()),
                                         password="1234567890abc")
    borrower, _ = Borrower.objects.get_or_create(user=user, phone_number="0951 {}".format(random.randint(1000, 9999)),
                                                 phone_number_mobile="0176 {}".format(random.randint(100000, 999999)))


def create_lender(first_name, last_name, user_name):
    website = "{}.{}".format(user_name.replace(' ', ''), random.choice(["de", "com", "org", "net"]))
    user, _ = User.objects.get_or_create(first_name=first_name, last_name=last_name, username=user_name,
                                         email='{}.{}@{}'.format(first_name.lower(), last_name.lower(), website),
                                         password="1234567890abc")
    lender, _ = Lender.objects.get_or_create(user=user, phone_number="0951 {}".format(random.randint(1000, 9999)),
                                             phone_number_mobile="0176 {}".format(random.randint(100000, 999999)),
                                             type=random.randint(0, 1),
                                             description="Ich bin {} {}, Nickname {}.".format(first_name, last_name,
                                                                                              user_name),
                                             website=website,
                                             location=get_random_location())


def create_categories():
    logger.debug("creating categories")
    create_category("Möbel")
    create_category("Küchengeräte")
    create_category("Werkzeug")
    create_category("Fläche")
    create_category("Veranstaltungsequipment")
    create_category("Elektronik & Technik")
    create_category("Büroartikel")
    create_category("Transportmittel")
    create_category("Spiel, Sport & Freizeit")
    logger.debug("done creating categories")


def create_category(title):
    category, _ = Category.objects.get_or_create(title=title)
    return category


def create_locations():
    streets = ["An der Weberei", "Zollnerstraße", "Memmelsdorfer Straße", "Gaustadter Hauptstraße", "Lange Straße",
               "Nürnberger Straße", "Geisfelder Straße"]

    for x in range(1, 10):
        house_number = random.choice(range(1, 15))
        street = random.choice(streets)
        title = '{} {}'.format(street, house_number)

        Location.objects.get_or_create(street=street, house_number=house_number,
                                       defaults=
                                       {'title': title,
                                        'longitude': None,
                                        'latitude': None})


def get_random_location():
    return random.choice(Location.objects.all())


def create_loan():
    number = random.randint(0, 10)
    rental_fee, _ = RentalFee.objects.get_or_create(interval_unit=number % 4, costs=number ^ 2)
    loan, _ = Loan.objects.get_or_create(caution=number, single_rent=number, rental_fee=rental_fee)
    return loan


def get_loan_agreement(item_type):
    loan_agreement_types = {Item.OBJECT: ["Leihvertrag_Objekt_1.pdf", "Leihvertrag_Objekt_2.pdf"],
                            Item.SERVICE: ["Vertrag_Dienstleistung_1.pdf", "Vertrag_Dienstleistung_2.pdf"],
                            Item.VENUE: ["Vertrag_Räumlichkeit_1.pdf", "Vertrag_Räumlichkeit_2.pdf"]}
    return load_loan_agreement(random.choice(loan_agreement_types[item_type]))


def load_image(filename, index):
    test_image_dir = os.path.join(BASE_DIR, 'static/test_images/')
    file_path = os.path.join(test_image_dir, filename)
    logger.info(file_path)
    reopen = open(file_path, 'rb')
    django_file = File(reopen)
    django_file.name = filename

    return Image.objects.create(file=django_file, order_id=index)


def load_images_for_item(item, images):
    for index, image_filename in enumerate(images):
        item.images.add(load_image(image_filename, index + 1))


def add_categories_to_item(item, categories):
    for category_title in categories:
        cat = create_category(category_title)
        if cat:
            item.categories.add(cat)


def load_loan_agreement(filename):
    test_loan_agreement_dir = os.path.join(BASE_DIR, 'static/test_loan_agreements/')
    file_path = os.path.join(test_loan_agreement_dir, filename)
    logger.info(file_path)
    reopen = open(file_path, 'rb')
    django_file = File(reopen)
    django_file.name = filename

    return LoanAgreement.objects.create(file=django_file)


def get_dimension(width, height, depth):
    return Dimension.objects.create(width=width, height=height,
                                    depth=depth)


def get_time_interval():
    start_time = datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(days=random.randint(0, 20))
    end_time = start_time + datetime.timedelta(days=random.randint(1, 7))
    time_interval, _ = TimeInterval.objects.get_or_create(start_time=start_time, end_time=end_time)
    return time_interval


def create_items():
    logger.debug("creating items")

    create_item_service("Workshop: Organisation einer öffentlichen Veranstaltung", ["course.jpg", "seminarRoom.jpg"],
                        ["Workshop"])

    create_item_object("Biertischgarnitur", ["beerTable.jpg"], ["Möbel"], get_dimension(2.2, 0.7, 0.9), 35, 20)
    create_item_object("gepolsteter Stuhl", ["chair.jpg"], ["Möbel"], get_dimension(0.6, 1.1, 0.7), 8, 30)
    create_item_object("Toaster", ["toaster.jpeg"], ["Küchengeräte"], get_dimension(0.25, 0.2, 0.25), 8, 1)
    create_item_object("Kamera Ausrüstung", ["cameraEquipment.jpg"], ["Elektronik & Technik"],
                       get_dimension(0.5, 0.5, 0.5), 15, 1)
    create_item_object("Lautsprecher (XLR)", ["speaker.jpg"], ["Elektronik & Technik", "Veranstaltungsequipment"],
                       get_dimension(0.4, 0.7, 0.35), 20, 2)
    create_item_object("Studio-Scheinwerfer", ["studioLight.jpg"], ["Elektronik & Technik", "Veranstaltungsequipment"],
                       get_dimension(0.35, 2, 0.35), 20, 3)
    create_item_object("Beamer FullHD", ["beamer.jpg"], ["Elektronik & Technik", "Veranstaltungsequipment"],
                       get_dimension(0.35, 2, 0.35), 20, 3)

    create_item_venue("Vortragssaal", ["lectureRoom.jpeg"], ["Saal"], get_dimension(30, 5, 15))
    create_item_venue("Seminarraum", ["seminarRoom_2.jpeg"], ["Seminarraum"], get_dimension(6, 3, 15))

    logger.debug("done creating items")


def get_abstract_item_fields(name):
    desc_parts = [
        "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.",
        "At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.",
        "Short"]
    description = " ".join(map(str, random.choices(desc_parts, k=2)))

    item = {
        'title': name,
        'description': description,
        'location': random.choice(Location.objects.all()),
        'lender': random.choice(Lender.objects.all()),
        'loan': create_loan(),
    }
    return item


def create_item_service(name, images, categories):
    base_item = get_abstract_item_fields(name)
    item_type = Item.SERVICE

    item_service, _ = Item.objects.get_or_create(**base_item, type=item_type,
                                                 loan_agreement=get_loan_agreement(item_type))

    load_images_for_item(item_service, images)
    add_categories_to_item(item_service, categories)


def create_item_object(name, images, categories, dimension, weight, amount):
    base_item = get_abstract_item_fields(name)
    item_type = Item.OBJECT

    item_object, _ = Item.objects.get_or_create(**base_item, type=item_type,
                                                loan_agreement=get_loan_agreement(item_type), dimension=dimension,
                                                weight=weight,
                                                amount=amount)
    load_images_for_item(item_object, images)
    add_categories_to_item(item_object, categories)


def create_item_venue(name, images, categories, dimension):
    base_item = get_abstract_item_fields(name)
    item_type = Item.VENUE

    item_venue, _ = Item.objects.get_or_create(**base_item, type=item_type,
                                               loan_agreement=get_loan_agreement(item_type), dimension=dimension)

    load_images_for_item(item_venue, images)
    add_categories_to_item(item_venue, categories)


def add_occupancies_to_items():
    items = Item.objects.all()
    for item in items:
        for i in range(random.randint(0, 2)):
            item.occupancies.add(get_time_interval())
