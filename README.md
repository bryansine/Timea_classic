# Timea Classic

Timea Classic is a Django-based e-commerce platform for baby shops, designed to streamline online sales and enhance customer experience

**Timea Classic: Ignite Your Baby Shop's Digital Frontier!**

Unleash the full potential of your baby shop with Timea Classic, a Django-powered e-commerce powerhouse meticulously crafted for the modern parent. We're not just building an online store; we're architecting an experience. Prepare to revolutionize your sales with:

* **Product Nirvana:**
    * Dive into a world of detailed product listings, where variants dance in perfect harmony.
    * Navigate a product universe with lightning-fast search and filtering, putting the perfect product at your customer's fingertips.
* **User Ascension:**
    * Fortified user authentication, safeguarding your customer's journey.
    * A seamless shopping cart experience, turning browsers into buyers.
    * Dynamic promotional content, that will keep customers engaged.
* **Marketing Mastery:**
    * Location-aware banner deployment, conquering every corner of your digital storefront.
    * Time-warp pop-ups, delivering critical messages with pinpoint precision.
    * Admin control that is simple, and effective.
* **Admin interface:**
    * Easy to use admin interface, allowing for the easy creation, and editing of promotions.

Timea Classic isn't just a platform; it's your digital ally in the fiercely competitive baby retail landscape. Dominate your niche, captivate your audience, and watch your sales soar.

---

## Timea Classic: Features That Empower Your Baby Shop

### Core Features: Foundation for Seamless E-commerce

* **Homepage**: Displays featured products and categories for immediate customer engagement.
* **Authentication**: Secure user registration, login, logout, and profile management.
* **Product Management**:
    * Detailed product listings with categories and variants.
    * Product details enriched with user reviews and dynamic star ratings.
* **Cart Management**: Easy addition, updating, and removal of items from the shopping cart.
* **Search Functionality**: Quick product discovery via name or category search.
* **Product Reviews**: Customer feedback and ratings displayed for informed purchasing.
* **Product Categories**: Organized product browsing for enhanced user experience.
* **Orders**: Streamlined order placement and customer feedback.

### Completed Features: Enhancements for Optimal Performance

* **User Profiles**: Users can now update their personal account details.
* **Payment Integration**: Secure payment processing enabled through integrated gateways (e.g., Stripe, PayPal).
* **Order Management**: Users can track their order history and access invoice generation.
* **Dynamic Promotions and Marketing Tools**:
    * Location based banner display, allowing for banners to be placed in any location of the website.
    * Timed pop up display, allowing for the display of time sensitive information.
* **Admin Control**:
    * Easy to use admin interface, allowing for the easy creation, and editing of promotions.
---

## Technologies Used

- **Backend**: Django 4.x
- **Frontend**: HTML, CSS , JavaScript, react js
- **Database**: PostgreSQL
- **Version Control**: Git & GitHub
- **Deployment**: PythonAnywhere

---

## Project Structure

- **Core App**: Handles authentication, homepage, settings, and general project functionalities.
- **Products App**: Manages product listings, product categories, and product variants.
- **Cart App**: Handles shopping cart logic and checkout processes.
- **Reviews App**: Manages product reviews and dynamic ratings.
- **Order App**: Handles order management, processing, and tracking.
- **Chat App**: Implements real-time chat functionality for customer support and communication.
- **Daraja App**: Integrates M-Pesa payment processing using the Daraja API.


---

## Installation


### Prerequisites

Before starting, make sure you have the following installed:

- Python (>= 3.8)
- PostgreSQL
- Git

To set up the project locally, follow these steps:

1. **Clone the project repository:**
 
   ```git clone https://github.com/bryansine/Timea_classic.git```
   
2.  Navigate to the project directory:
  ``` cd timea_classic/```
3. Create a Virtual Environment:
 ``` python3 -m venv myvenv```
4.  Activate the Virtual Environment (macOS/Linux):
  ```source myvenv/bin/activate```
5.  Install Required Packages:
 ``` pip install -r requirements.txt```
6.  Migrate the Database:
  ```python manage.py migrate```
7.  Create a Super User:
  ```python manage.py createsuperuser```
8.  Start the Development Server:
 ``` python3 manage.py runserver```


## Contributing

I welcome contributions from the community. If you encounter any bugs or have feature requests, please submit them through GitHub issues.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

**Author:** Bryan Sine
**LinkedIn:** [Bryan Sine](https://www.linkedin.com/in/bryansine)
