import React from "react";
import { useState, useEffect } from "react";
import AnchorLink from "react-anchor-link-smooth-scroll";
import useMediaQuery from "../hooks/useMediaQuery";
import menuIcon from "../assets/menu.png";
import closeIcon from "../assets/close-icon.svg";
import { AnimatePresence, motion, useCycle } from "framer-motion";
import SocialMediaIcons from "../components/SocialMediaIcons";

const Link = ({ page, selectedPage, setSelectedPage }) => {
    const lowerCasePage = page.toLowerCase();

    return (
      <AnchorLink
        className={`${
          selectedPage === lowerCasePage ? "lg:text-black text-pumpkin" : ""
        } hover:text-brown-red transition duration-500`}
        href={`#${lowerCasePage}`}
        onClick={() => setSelectedPage(lowerCasePage)}
      >
        {page}
      </AnchorLink>
    );
  };

const Navbar = ({ isTopOfPage, selectedPage, setSelectedPage }) => {
    const [isMenuToggled, setIsMenuToggled] = useState(false);
    const isAboveSmallScreens = useMediaQuery("(min-width: 768px)");
    const navbarBackground = isTopOfPage ? "sm:backdrop-blur bg-cosmicwhite" : "md:backdrop-blur-lg opacity-95";


    useEffect(() => {
        if (isMenuToggled) {
          document.body.style.overflow = 'hidden'
        }
      }, [isMenuToggled])
    useEffect(() => {
        if (!isMenuToggled) {
          document.body.style.overflow = 'auto'
        }
      }, [!isMenuToggled])



    return (
        <motion.nav className={`${navbarBackground} transition duration-500 ease-in-out w-full md:fixed top-0 py-3 lg:z-30`}>
            <div className="flex items-center justify-between mx-auto w-5/6">
                <h4 className="font-playfair text-4xl font-bold text-jet">A/D</h4>

                {/* Desktop Navigation */}
                {isAboveSmallScreens ? (
                    <div className="flex justify-between gap-16 font-montserrat text-sm font-semibold text-black">
                        <Link page="Home" selectedPage={selectedPage} setSelectedPage={setSelectedPage}/>

                        <Link page="Skills" selectedPage={selectedPage} setSelectedPage={setSelectedPage}/>

                        <Link page="Designs" selectedPage={selectedPage} setSelectedPage={setSelectedPage}/>

                        <Link page="Contact" selectedPage={selectedPage} setSelectedPage={setSelectedPage}/>
                    </div>
                    ) : (
                    <button className="p-2 max-w-[48px] max-h-[48px] z-10" onClick={() => setIsMenuToggled(!isMenuToggled)}>
                            <img alt="menu-icon" src={menuIcon} />
                    </button>
                    )}


                {/* Mobile Menu PopUp */}
                {!isAboveSmallScreens && isMenuToggled && (
                    <motion.div
                    initial={{ width: 0 }} animate={{ width: 300 }}
                    transition={{ type: "spring", bounce: 0.1, duration: 1 }}
                    className="fixed right-0 bottom-0 h-full bg-black opacity-95 transition duration-500 ease-in-out w-full z-20">
                        {/* Close Icon */}
                        <motion.div className="flex justify-start p-12">
                            <button onClick={() => setIsMenuToggled(!isMenuToggled)}>
                                <img className="scale-100" alt="close-icon" src={closeIcon} />
                            </button>
                        </motion.div>

                        {/* Menu Items */}
                        <motion.div className="flex flex-col gap-8 mx-auto pl-14 text-xs font-medium font-montserrat text-cosmicwhite hover:text-brown-red" onClick={() => setIsMenuToggled(!isMenuToggled)}>

                            <a href="https://youtu.be/XUn7xBrK0gI">Monza '21</a>

                            <a href="https://youtu.be/kkTymGMAfgU">Mirror Mirror</a>

                            <a href="https://youtu.be/6POZlJAZsok">Just The Two Of US</a>

                            <a href="https://open.spotify.com/playlist/2c4XD9EPoeHDqqTXKWzzJV?si=98bd5ec7b2d442ec">HonkyTonk</a>

                            <div className="invert scale-75 absolute bottom-28 left-0 ml-2 opacity-85">
                              <SocialMediaIcons />
                            </div>

                            <p className="text-cosmicwhite font-light text-xs pb-5 font-montserrat opacity-70 absolute inset-x-10 bottom-20">© Anurag Das 2023</p>

                        </motion.div>
                    </motion.div>
                )}
            </div>
        </motion.nav>
    );
};

export default Navbar;
