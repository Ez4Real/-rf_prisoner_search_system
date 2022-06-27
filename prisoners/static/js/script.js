const loginForm = document.getElementById('login_form')
const registerForm = document.getElementById('register_form')

const modal = document.getElementById('family_relation_request_modal')
const requestButton = document.getElementById('request_button')
const closeButton = modal?.querySelector('.close')
const familyRelationForm = modal?.querySelector('#family_relation_request_form')
const familyRelationStatus = modal?.querySelector('.family_relation_status')

const reviewModal = document.getElementById('review_request_modal')
const reviewButton = document.getElementById('review_button')
const reviewCloseButton = reviewModal?.querySelector('.close')
const reviewRequestForm = reviewModal?.querySelector('#review_request_form')
const reviewStatus = reviewModal?.querySelector('.review_status')


const modalOpen = () => {
    modal.style.display = "block"
}
closeButton && closeButton.addEventListener('click', function() {
    modal.style.display = "none";
})
window.addEventListener('click', function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
  }
}) 
requestButton && requestButton.addEventListener('click', modalOpen)


const reviewModalOpen = () => {
    reviewModal.style.display = "block"
}
reviewCloseButton && reviewCloseButton.addEventListener('click', function() {
    reviewModal.style.display = "none";
})
window.addEventListener('click', function(event) {
    if (event.target == reviewModal) {
        reviewModal.style.display = "none";
  }
}) 
reviewButton && reviewButton.addEventListener('click', reviewModalOpen)


function serializeFormData(form, isregister) {
    const fields = form.elements
    const formData = new FormData()

    for (let i = 0; i < fields.length; i++) {
        const element = fields[i] 
        if (element.value) {
            if (element.name === 'email' && !isregister) {
                formData.append('username', element.value)
            } else {
                formData.append(element.name, element.value)
        }}
    }
    return formData
}


async function reviewRequest(type) {
    let responce;

    const requestId = location.pathname.split('/').pop()
    if (type == 'confirm') {
        responce = await fetch(`/requests/confirm/${requestId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        })
        reviewStatus.textContent = 'Запит успішно підтверджено'
    } else {
        responce = await fetch(`/requests/decline/${requestId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
        })
        reviewStatus.textContent = 'Запит успішно скасовано'
    }
        setTimeout(() => {
            reviewModal.style.display = "none";
        }, 1500)
}


const getCountryCode = async () => {
    try {
      const response = await fetch("https://ipapi.co/json/");
      const data = await response.json();
      return data && data.country ? data.country : null;
    } catch (error) {
      return null;
    }
  };


registerForm && registerForm.addEventListener('submit', async (e) => {
    e.preventDefault()
    const currentCountry = await getCountryCode()
    if (currentCountry !== 'UA') return 
    const data = serializeFormData(e.target, true)
    if (data.get('password') !== data.get('psw-repeat')) return 
    const responce = await fetch('/users', {
        method: 'POST',
        body: data
    })
    const result = await responce.json()
    if (responce.status === 200) {
        window.location.href='/auth/login'
    } else {
        e.target.querySelector('.error-message').textContent = result.detail
    }
    console.log(result)
}) 


document.querySelector('select[name=family_relation]')?.addEventListener('change', (e) => {
    const familyRelationInput = familyRelationForm.querySelector('input[name=family_relation]')
    if (e.target.value === 'another') {
        if (familyRelationInput) {
            return
        }
        const input = document.createElement('input')
        input.name = 'family_relation'
        input.placeholder = 'Укажите вашу родственную связь'
        e.target.after(input)
    } else {
        if (familyRelationInput) {
            familyRelationInput.remove()
        }
    }
})


familyRelationForm && familyRelationForm.addEventListener('submit', async (e) => {
    e.preventDefault()
    console.log(e.target['family_relation'].value)

    const prisonerId = location.pathname.split('/').pop()
    const data = serializeFormData(e.target, true)
    console.log(data)
    const responce = await fetch(`/prisoners/request/${prisonerId}`, {
        method: 'POST',
        body: data,
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
    })
    if (responce.status === 200) {
        familyRelationStatus.textContent = 'Запрос отправлен'
        setTimeout(() => {
            modal.style.display = "none";
        }, 1500)
    } 
}) 


reviewRequestForm && reviewRequestForm.querySelectorAll('button[type=submit]').forEach(button => {
    button.addEventListener('click', async (e) => {
        await reviewRequest(e.target.dataset.type)
})
    // if (responce.status === 200) {
             
    // }
}) 


loginForm && loginForm.addEventListener('submit', async (e) => {
    e.preventDefault()
    const data = serializeFormData(e.target)
    const responce = await fetch('/users/token', {
        method: 'POST',
        body: data
    })
    const result = await responce.json()
    localStorage.setItem('access_token', result.access_token)
    localStorage.setItem('role', result.role)
    if (responce.status === 200) {
        window.location.href='/prisoners'
    }
    else {
        e.target.querySelector('.error-message').textContent = result.detail
    }
    console.log(result)
}) 


const prisoners = document.querySelectorAll('.prisoner_url')
prisoners && prisoners.forEach((prisoner) => {
    prisoner.addEventListener('click', async (e) =>{
        const prisonerId = e.target.getAttribute('data-prisoner-id')
        window.location.href=`/prisoners/${prisonerId}`
    })
})


const requests = document.querySelectorAll('.request')
requests && requests.forEach((request) => {
    request.addEventListener('click', async (e) =>{
        const requestId = e.target.getAttribute('data-request-id')
        window.location.href=`/requests/${requestId}`
    })
})


const requestsRedirect = document.getElementById('requests')
// requestsRedirect && requestsRedirect.addEventListener('click', async (e) => {
//     e.preventDefault()
//     const responce = await fetch(`/requests`, {
//         method: 'GET',
//         headers: {
//             'Authorization': `Bearer ${localStorage.getItem('access_token')}`
//         }
//     })
//     if (responce.status === 200) {
//         window.location.href='/requests'
//     } 
// })


window.addEventListener('DOMContentLoaded', () => {
    const role = localStorage.getItem('role')
    if (role !== 'admin') {
        requestsRedirect.style.display = 'none'
    }
})