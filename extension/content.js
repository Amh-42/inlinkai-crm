// --- IMPORTANT ---
// Selectors are based on the LARGE HTML snippet provided (June 2024).
// LinkedIn WILL change its structure. These WILL break. Constant inspection
// and updating using developer tools is REQUIRED.
// Using data attributes (data-test-*) is preferred if available and stable.
// --- ----------- ---
async function scrapeProfileData() {
    console.log("LinkedIn CRM Scraper: Starting extraction...");

    // --- Helper Functions ---
    const getText = (selector, element = document) => element.querySelector(selector)?.innerText?.trim() || null;
    const getAttribute = (selector, attribute, element = document) => element.querySelector(selector)?.[attribute] || null;
    const getAllText = (selector, element = document) => Array.from(element.querySelectorAll(selector)).map(el => el.innerText?.trim()).filter(Boolean);
    const getFullTextFromSeeMore = (containerSelector) => {
        const container = document.querySelector(containerSelector);
        if (!container) return null;
        // Try to find the hidden span first (often used for full text)
        let fullText = container.querySelector('span.visually-hidden')?.innerText?.trim();
        if (fullText) return fullText;
        // Fallback: get the visible part + potentially hidden parts
        fullText = Array.from(container.querySelectorAll('span[aria-hidden="true"]')).map(s => s.innerText?.trim()).join('\n');
        // Simple cleanup for "…see more" or similar text if needed (might need adjustment)
        return fullText?.replace(/…see more$|…\s?less$/i, '')?.trim() || null;
    };

    // --- Top Card Extraction ---
    console.log("Extracting Top Card...");
    const profileData = {
        linkedin_url: window.location.href,
        name: getText('.pv-text-details__left-panel h1') || getText('h1'), // More specific first
        headline: getText('div.text-body-medium.break-words'),
        location: getText('span.text-body-small.inline.t-black--light.break-words'),
        profile_pic_url: getAttribute('.pv-top-card-profile-picture__image--show', 'src') || 
                        getAttribute('.pv-top-card-profile-picture__container img', 'src') || 
                        getAttribute('img.profile-photo-edit__preview', 'src') || 
                        getAttribute('.pv-top-card-profile-picture__image', 'src'),
        banner_pic_url: getAttribute('img#profile-background-image-target-image', 'src') || getAttribute('.profile-banner__image', 'src'),
        website: getAttribute('section.pv-top-card--website a', 'href'),
        followers: null, // Parse later
        connections: null, // Parse later
    };

    // Parse Followers/Connections
    const followConnectList = document.querySelector('ul.ThzRmIxXqMeRYkZELxulmxZlbOizcYNbyqrCI');
    if (followConnectList) {
        followConnectList.querySelectorAll('li span.t-bold').forEach(span => {
            const text = span.parentElement?.innerText?.toLowerCase() || '';
             if (text.includes('follower')) {
                 profileData.followers = span.innerText.trim();
             } else if (text.includes('connection')) {
                 profileData.connections = span.innerText.trim();
             }
        });
    }
     console.log("Top Card Data:", profileData);


    // --- About Section ---
     console.log("Extracting About...");
    const aboutSection = document.getElementById('about');
    if (aboutSection) {
         // Try to get the full text from the visually-hidden span which often contains complete content
         profileData.about = getText('#about + div .inline-show-more-text--is-collapsed span.visually-hidden') ||
                           getText('.inline-show-more-text--is-collapsed span.visually-hidden');
         
         // Fallbacks if the above doesn't work
         if (!profileData.about) {
             profileData.about = getFullTextFromSeeMore('#about + div .inline-show-more-text--is-collapsed');
         }
         if (!profileData.about) {
             profileData.about = getFullTextFromSeeMore('#about div.display-flex.ph5.pv3 div[class*="inline-show-more-text"]');
         }
     }
     console.log("About:", profileData.about ? profileData.about.substring(0, 50) + '...' : 'N/A');


    // --- Featured Section ---
    console.log("Extracting Featured...");
    profileData.featured = [];
    const featuredSection = document.getElementById('featured');
    if (featuredSection) {
        const items = featuredSection.querySelectorAll('.pvs-carousel .artdeco-carousel__item');
        items.forEach(item => {
            const featuredItem = {
                title: getText('.pvs-media-content__preview .text-heading-small', item),
                link: getAttribute('a.optional-action-target-wrapper', 'href', item), // May need refinement
                description: getText('.pvs-media-content__preview .text-body-small', item),
                image_url: getAttribute('.pvs-media-content__image img', 'src', item),
                type: getText('.pvs-content__top-bar span[aria-hidden="true"]', item) || 'Unknown' // e.g., Link, Post
            };
             if (featuredItem.title || featuredItem.description) {
                 profileData.featured.push(featuredItem);
             }
        });
    }
     console.log(`Featured Items Found: ${profileData.featured.length}`);


    // --- Experience Section ---
    console.log("Extracting Experience...");
    profileData.experience = [];
    const experienceSection = document.getElementById('experience');
    if (experienceSection) {
        const experienceItems = experienceSection.querySelectorAll(':scope > .RMMjdDQVaUTNlcsWDNPAmMYRlRGovicFIUBvchg > ul > li.artdeco-list__item');
        experienceItems.forEach(item => {
            const companyElement = item.querySelector('div[data-view-name="profile-component-entity"]');
            if (!companyElement) return; // Skip if basic structure missing

            const companyNameElem = companyElement.querySelector('.hoverable-link-text span[aria-hidden="true"]'); // Usually company name here for multi-role
            const companyNameSingle = getText('span.t-14.t-normal span[aria-hidden="true"]', companyElement)?.split('·')[0]?.trim(); // For single role
            let companyName = companyNameElem ? companyNameElem.innerText.trim() : companyNameSingle;

            // Check for multiple roles within the same company (nested list items)
            const roles = item.querySelectorAll(':scope > div > div.pvs-entity__sub-components li[class*="pvs-list__item--with-top-padding"]'); // Example selector for sub-roles

            if (roles.length > 0) {
                 // Multi-role entry - capture company info once if needed, then loop roles
                 roles.forEach(roleItem => {
                    const exp = {
                        title: getText('.hoverable-link-text span[aria-hidden="true"]', roleItem),
                        company_name: companyName,
                        company_linkedin_url: getAttribute('a[data-field="experience_company_logo"]', 'href', item), // From parent item
                        employment_type: companyNameSingle?.includes('·') ? companyNameSingle.split('·')[1]?.trim() : null, // Try to get from single role line if exists
                        location: null, // Parse from date/location lines
                        start_date: null,
                        end_date: null,
                        duration: null,
                        description: getFullTextFromSeeMore('div[class*="inline-show-more-text"]', roleItem),
                        is_multi_role: 1, // Flag as part of multi-role
                        parent_experience_id: null // Could link if needed, complex
                    };
                    // Parse Dates/Location/Duration for sub-role
                    const dateLocationLines = getAllText('span.t-14.t-normal.t-black--light span[aria-hidden="true"]', roleItem);
                     dateLocationLines.forEach(line => {
                        if (line.match(/\w+ \d{4} - (\w+ \d{4}|Present)/)) { // Date matching
                            const dates = line.split('·')[0].trim().split(' - ');
                            exp.start_date = dates[0];
                            exp.end_date = dates[1];
                            exp.duration = line.split('·')[1]?.trim();
                        } else if (line.includes('·')) { // Likely Location · Remote/Onsite
                            exp.location = line;
                        }
                     });
                    if(exp.title) profileData.experience.push(exp);
                 });
            } else {
                // Single role entry or simple structure
                const exp = {
                    title: getText('.hoverable-link-text span[aria-hidden="true"]', companyElement),
                    company_name: companyName,
                    company_linkedin_url: getAttribute('a[data-field="experience_company_logo"]', 'href', companyElement),
                    employment_type: null, // Parse from text line
                    location: null, // Parse from text line
                    start_date: null,
                    end_date: null,
                    duration: null,
                    description: getFullTextFromSeeMore('div[class*="inline-show-more-text"]', companyElement) || getFullTextFromSeeMore('div[class*="inline-show-more-text"]', item), // Check both levels
                    is_multi_role: 0
                };

                // Parse Employment Type, Dates, Location from the text lines
                const textLines = getAllText('span.t-14.t-normal span[aria-hidden="true"], span.t-14.t-normal.t-black--light span[aria-hidden="true"]', companyElement);
                textLines.forEach(line => {
                    if (line.includes('·') && (line.toLowerCase().includes('full-time') || line.toLowerCase().includes('part-time') || line.toLowerCase().includes('self-employed') || line.toLowerCase().includes('contract'))) {
                        const parts = line.split('·');
                        if (!exp.company_name) exp.company_name = parts[0]?.trim(); // Might get company name here too
                        exp.employment_type = parts[1]?.trim();
                    } else if (line.match(/\w+ \d{4} - (\w+ \d{4}|Present)/)) { // Date matching
                       const dates = line.split('·')[0].trim().split(' - ');
                       exp.start_date = dates[0];
                       exp.end_date = dates[1];
                       exp.duration = line.split('·')[1]?.trim();
                    } else if (line.match(/[\w\s]+, [\w\s]+, [\w\s]+/) || line.match(/[\w\s]+, [\w\s]+/) || line.includes('Remote') || line.includes('On-site')) { // Location guess
                        exp.location = line;
                    }
                });
                 if(exp.title || exp.company_name) profileData.experience.push(exp);
            }
        });
    }
     console.log(`Experience Items Found: ${profileData.experience.length}`);


    // --- Education Section ---
    console.log("Extracting Education...");
    profileData.education = [];
    const educationSection = document.getElementById('education');
    if (educationSection) {
        const educationItems = educationSection.querySelectorAll(':scope > .RMMjdDQVaUTNlcsWDNPAmMYRlRGovicFIUBvchg > ul > li.artdeco-list__item');
        educationItems.forEach(item => {
             const edu = {
                 school_name: getText('.hoverable-link-text span[aria-hidden="true"]', item),
                 school_linkedin_url: getAttribute('a.optional-action-target-wrapper', 'href', item), // Assuming first link is school
                 degree_name: null,
                 field_of_study: null,
                 start_date: null,
                 end_date: null,
                 grade: null,
                 activities: null,
                 description: getFullTextFromSeeMore('div[class*="inline-show-more-text"]', item) // Look for description block
             };

             // Parse Degree, Field, Dates from text lines
             const textLines = getAllText('span.t-14.t-normal span[aria-hidden="true"], span.t-14.t-normal.t-black--light span[aria-hidden="true"]', item);
             textLines.forEach(line => {
                 if (line.includes(',') && (line.toLowerCase().includes('bachelor') || line.toLowerCase().includes('master') || line.toLowerCase().includes('phd') || line.toLowerCase().includes('degree') || line.toLowerCase().includes(' B.S') || line.toLowerCase().includes(' BS,'))) {
                     const parts = line.split(',');
                     edu.degree_name = parts[0]?.trim();
                     edu.field_of_study = parts.slice(1).join(',').trim();
                 } else if (line.match(/\w+ \d{4} - (\w+ \d{4}|\d{4})/)) { // Date matching
                     const dates = line.split(' - ');
                     edu.start_date = dates[0]?.trim();
                     edu.end_date = dates[1]?.trim();
                 } else if (line.toLowerCase().startsWith('grade:')) {
                     edu.grade = line.substring(6).trim();
                 } else if (line.toLowerCase().startsWith('activities and societies:')) {
                     edu.activities = line.substring(25).trim();
                 }
             });
             // If degree/field not parsed above, try the line just below school name
              if (!edu.degree_name && !edu.field_of_study) {
                  const degreeLine = getText('span.t-14.t-normal:not(.t-black--light) span[aria-hidden="true"]', item);
                  if(degreeLine && !degreeLine.includes(edu.school_name)){ // Make sure it's not just repeating school name
                       const parts = degreeLine.split(',');
                       edu.degree_name = parts[0]?.trim();
                       edu.field_of_study = parts.slice(1).join(',').trim();
                  }
              }


             if (edu.school_name) {
                 profileData.education.push(edu);
             }
        });
    }
    console.log(`Education Items Found: ${profileData.education.length}`);


    // --- Skills Section ---
    console.log("Extracting Skills...");
    profileData.skills = [];
    const skillsSection = document.getElementById('skills');
    if (skillsSection) {
        // Simpler structure usually: list of skills directly
         const skillItems = skillsSection.querySelectorAll('.RMMjdDQVaUTNlcsWDNPAmMYRlRGovicFIUBvchg > ul > li');
         skillItems.forEach(item => {
             const skillName = getText('.hoverable-link-text span[aria-hidden="true"]', item);
             if (skillName && !skillName.toLowerCase().startsWith('show all')) {
                 profileData.skills.push(skillName);
             }
         });
    }
    
    // Look for top skills in the About section if main Skills section hasn't found anything
    if (profileData.skills.length === 0 && aboutSection) {
        // Look for the specific top skills section shown in example HTML
        const topSkillsText = getText('.display-flex.align-items-center.t-14.t-normal span[aria-hidden="true"]', aboutSection.parentElement) ||
                             getText('.display-flex.align-items-center.t-14.t-normal span[aria-hidden="true"]');
                             
        if (topSkillsText && !topSkillsText.toLowerCase().includes('top skills')) {
            profileData.skills = topSkillsText.split('•').map(s => s.trim()).filter(Boolean);
        }
        
        // Fallback for different HTML structure
        if (profileData.skills.length === 0) {
            const topSkillsText = getText('[data-view-name="profile-component-entity"] span:not(.t-bold)', aboutSection.parentElement) ||
                                 getText('.artdeco-card [data-view-name="profile-component-entity"] span:not(.t-bold)');
            if (topSkillsText && !topSkillsText.toLowerCase().includes('top skills')) {
                profileData.skills = topSkillsText.split('•').map(s => s.trim()).filter(Boolean);
            }
        }
    }
    console.log(`Skills Found: ${profileData.skills.length}`);


    // --- Recommendations Section (Received) ---
    console.log("Extracting Recommendations...");
    profileData.recommendations = [];
    const recommendationsSection = document.getElementById('recommendations');
    if (recommendationsSection) {
        // Find the 'Received' tabpanel - it might not always be ember424
        const receivedPanel = recommendationsSection.querySelector('.artdeco-tabpanel.active') || recommendationsSection.querySelector('.artdeco-tabpanel:not([hidden])'); // Active or first visible
        if(receivedPanel){
             const recommendationItems = receivedPanel.querySelectorAll(':scope > div > ul > li.artdeco-list__item'); // Adjust selector based on actual structure
             recommendationItems.forEach(item => {
                const rec = {
                    recommender_name: getText('.hoverable-link-text span[aria-hidden="true"]', item),
                    recommender_headline: getText('span.t-14.t-normal span[aria-hidden="true"]', item), // Usually the line below name
                    recommender_linkedin_url: getAttribute('a.optional-action-target-wrapper', 'href', item),
                    relationship: getText('span.t-14.t-normal.t-black--light span[aria-hidden="true"]', item), // The line with date/relationship
                    recommendation_text: getFullTextFromSeeMore('div[class*="inline-show-more-text"]', item)
                };
                 if (rec.recommender_name && rec.recommendation_text) {
                     profileData.recommendations.push(rec);
                 }
             });
        }
    }
    console.log(`Recommendations Found: ${profileData.recommendations.length}`);


    // --- Send Data ---
    console.log("Scraping finished. Sending data to backend...");
    const apiUrl = 'https://3rm.inlinkai.com/api/save_profile';

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData),
        });
        const result = await response.json();

        if (response.ok && result.success) {
            console.log('Profile saved successfully:', result.message);
            alert("Profile data sent to backend!");
        } else {
            console.error('Failed to save profile:', result.error || `HTTP ${response.status}`);
            alert(`Failed to save profile: ${result.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error sending data to backend:', error);
        alert(`Error sending data: ${error.message}`);
    }
}

// --- Execute ---
scrapeProfileData();