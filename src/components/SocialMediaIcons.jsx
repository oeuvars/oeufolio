import React from 'react';
import medium from "../assets/Icons/medium.svg";
import instagram from "../assets/Icons/instagram.svg";
import twitter from "../assets/Icons/twitter.svg";
import github from "../assets/Icons/github.svg";

const SocialMediaIcons = () => {
    return (
        <div className="flex justify-center md:justify-start my-10 gap-7">
            <a className="hover:opacity-50 transition duration-500 scale-90" href="https://www.instagram.com/oeuvars" target="_blank" rel="noreferrer"><img alt="linkedin-link" src={instagram}/></a>
            <a className='hover:opacity-50 transition duration-500 scale-90' href="https://twitter.com/Oeuvars" target="_blank" rel="noreferrer"><img alt="twitter-link" src={twitter}/></a>
            <a className='hover:opacity-50 transition duration-500 scale-90' href="https://www.medium.com/@oeuvars" target="_blank" rel="noreferrer"><img alt="linkedin-link" src={medium}/></a>
            <a className='hover:opacity-50 transition duration-500 scale-90' href="https://www.github.com/oeuvars" target="_blank" rel="noreferrer"><img alt="linkedin-link" src={github}/></a>
        </div>
    )
}

export default SocialMediaIcons;
