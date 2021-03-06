var BookingId = null;
var SelectedFacilityId = null;
var SelectedYear = null;
var SelectedMonth = null;
var SelectedDay = null;

var PageType_Landing = "1";
var PageType_Details = "2";
var PageType_Current = null;
var IsUserAuthenticated = false;

$(document).ready(function () {

	PageType_Current = $('#hdnPageType').val();
	
	if (PageType_Current === PageType_Landing) {
		//Landing Page
		populateUserAuthenticated();

		getMyBookingsCount();

		$('#tabBookings button').click(function (e) {
			e.preventDefault();
			$('#tabBookings button').removeClass('active');
			$(this).addClass('active');
			$('.material-tab-panel').toggleClass('hide');
		});
	}
	else if (PageType_Current === PageType_Details) {
		// Detail page
		IsUserAuthenticated = true;
		BookingId = $('#hdnBookingId').val();
		loadBookingDetailsData();
	}

	checkSuspension();
	getBookingProductImages();
	
});

//-------- Landing Page --------------------------------

function populateUserAuthenticated() {
	let authText = $('#hdnUserAuthenticated').val().toLowerCase();

	if (authText === 'true') {
		IsUserAuthenticated = true;
	}
	else {
		IsUserAuthenticated = false;
	}
}

function getMyBookingsCount() {
	if (IsUserAuthenticated === true) {
		$.get('/booking/mybookings/count').done(function (response) {
			if (response !== 0) {
				$('.my-bookings-count').html('(' + response + ')');
				getMyBookings();

				if (response > 3) {
					$('.all-bookings-link').removeClass('hidden');
				}
			}
			else {
				$('#divNoBookings-large').removeClass('hidden');
				$('.all-bookings-link').addClass('hidden');
			}
		});
	}
	else {
		$('#divNoBookings-large').removeClass('hidden');
		$('.all-bookings-link').addClass('hidden');
	}
}

function getBookingProductImages() {
	let productSet = new Set(); // Unique elemets collection
	let imagesToFetch = new Set($('.booking-product-image'));

	for (const imgElem of imagesToFetch) {
		productSet.add($(imgElem).data('product-id'));
	}

	for (const productId of productSet) {
		getBookingProductImage(productId);
	}
}

function getBookingProductImage(productId) {
	GetProductImage(productId, imageCallback, productId)
}

function imageCallback(response, productId) {
	$('.booking-product-image[data-product-id=' + productId + ']').attr('src', response.Image);
	$('.booking-product-image[data-product-id=' + productId + ']').attr('alt', response.AltText);
}

function getMyBookings() {
	$.get('/booking/mybookings/3').done(function (response) {
		$('#divMyBookings-large').html(response);
		$('#divmybookings-small').html(response);
	});
}

function ConfirmCancelBooking(btn) {
	openCancellationModal($(btn).data('booking-participant-id'), $(btn).data('product-facility-name'), $(btn).data('booking-day'), $(btn).data('booking-time'))
}

//-------- End of Landing Page --------------------------------

//-------- Detail Page ----------------------------------------

function loadBookingDetailsData() {
	let dateSelectorPromise = new Promise(loadDateSelector);
	let facilitiesPromise = new Promise(loadFacilities);

	Promise.all([dateSelectorPromise, facilitiesPromise]).then(function () {
		loadBookingSlots();
	});
}

function loadDateSelector(resolve, reject) {
	$.get('/booking/' + BookingId + '/dates').done(function (response) {
		$('#divBookingDateSelector').html(response);
		setActiveDate();
		resolve();
	}).fail(function () {
		reject();
	});
}

function loadFacilities(resolve, reject) {
	$.get('/booking/' + BookingId + '/facilities').done(function (response) {
		$('#divBookingFacilities').html(response);
		setActiveFacility();
		setSelectedFacilityLabel();
		attachTabChangeEventHadlers();
		resolve();
	}).fail(function () {
		reject();
	});
}

function attachTabChangeEventHadlers() {
	$('#tabBookingFacilities button').click(function (e) {
		$('#tabBookingFacilities button').removeClass('active');
		$(this).addClass('active');
		$('#hdnSelectedFacilityId').val($(this).data('facility-id'));
		setActiveFacility();
		loadBookingSlots();
	});
}

function BookingFacilityChanged(btn) {
	$('.booking-facility-list').removeClass('active bg-primary');
	$('.booking-facility-list > span.glyphicon').addClass('hidden');
	$(btn).addClass('active bg-primary');
	$(btn.children).removeClass('hidden')
}

function BookingFacilityChangeApply() {
	$('#hdnSelectedFacilityId').val($('.booking-facility-list.active').data('facility-id'));
	setActiveFacility();
	setSelectedFacilityLabel();
	loadBookingSlots();
	$('#modalBookingFacilities').modal('hide');
}

function BookingDateChanged() {
	// This callback defined via SingleDateSelector control.
	setActiveDate();
	loadBookingSlots();
}

function loadBookingSlots() {
	$('#divBookingSlots').html('');
	$.get('/booking/' + BookingId + "/slots/" + SelectedFacilityId + "/" + SelectedYear + "/" + SelectedMonth + "/" + SelectedDay).done(function (response) {
		$('#divBookingSlots').html(response);
	});
}

function setActiveFacility() {
	SelectedFacilityId = $('#hdnSelectedFacilityId').val();
}

function setSelectedFacilityLabel() {
	$('#spanSelectedFacility').html($('.booking-facility-list.active').data('facility-name'));
}

function setActiveDate() {
	SelectedYear = $('#hdnDateSelectorYear').val();
	SelectedMonth = $('#hdnDateSelectorMonth').val();
	SelectedDay = $('#hdnDateSelectorDay').val();

	$('#spanSelectedDate').html($('#hdnDateSelectorDateText').val());
}

function Reserve(appointmentId, timeSlotId, timeSlotInstanceId, slotNumber) {
	$('.booking-slot-item[data-slot-number=' + slotNumber + '] .booking-slot-action-item button').attr('disabled', 'disabled').html('Booking...');

	let postData = {
		bookingId: BookingId,
		facilityId: SelectedFacilityId,
		appointmentId: appointmentId,
		timeSlotId: timeSlotId,
		timeSlotInstanceId: timeSlotInstanceId,
		year: SelectedYear,
		month: SelectedMonth,
		day: SelectedDay
	};

	$.post('/booking/reserve', postData).done(function (response) {
		if (response.Success === true) {
			loadBookingSlots();
			$('.booking-detail-alert').hide();
			$('#alertBookingSuccess').show();
		}
		else {
			handleBookingError(response);
		}
	}).fail(function (response) {
		handleBookingError();
	});
}

const handleBookingError = (response) => {
	loadBookingSlots();
	$('.booking-detail-alert').hide();
	if (response.ErrorCode === 1) {
		$('#alertBookingFailure-NoSpots').show();
	}
	else {
		$('#alertBookingFailure').show();
	}
}

function ConfirmBookingCancelFromDetails(slotNumber, slotTime) {
	let participantId = $('.booking-slot-item[data-slot-number=' + slotNumber + ']').data('participant-id');

	let productAndFacilityName = $('#hdnBookingProductName').val() + '';
	let bookingDay = $('#hdnDateSelectorDateText').val();
	openCancellationModal(participantId, productAndFacilityName, bookingDay, slotTime);
}
//-------- End of Detail Page ---------------------------------


//------- Common Methods -------------------------------------------------

function openCancellationModal(id, productAndFacilityName, bookingDay, bookingTime) {
	$('#modalCancelBooking #bookingName').html(productAndFacilityName);
	$('#modalCancelBooking #bookingDay').html(bookingDay);
	$('#modalCancelBooking #bookingTime').html(bookingTime);
	$('#modalCancelBooking').modal('show');
	$('#modalCancelBooking #hdnBookingParticipantId').val(id);
}

function CancelBooking() {
	let bookingId = $('#modalCancelBooking #hdnBookingParticipantId').val();
	let originalCancelText = $('#modalCancelBooking #btnCancelBooking').html();
	$('#modalCancelBooking #btnCancelBooking').attr('disabled', 'disabled').html('Cancelling...');

	$.ajax({
		url: '/booking/delete/' + bookingId,
		type: 'POST'
	}).done(function (response) {
		$('#modalCancelBooking').modal('hide');
		if (response === true) {
			if (PageType_Current === PageType_Landing) {
				$('.mybooking-card[data-booking-id=' + bookingId + ']').remove();
				getMyBookingsCount(); // Refresh my bookings section
			}
			else if (PageType_Current === PageType_Details) {
				loadBookingSlots();
				$('.booking-detail-alert').hide();
				$('#alertBookingCancellationSuccess').show();
			}
		}
	}).then(function () {
		// cleanup cancel modal
		$('#modalCancelBooking #btnCancelBooking').removeAttr('disabled').html(originalCancelText);
		$('#modalCancelBooking #bookingName').html('');
		$('#modalCancelBooking #bookingDay').html('');
		$('#modalCancelBooking #bookingTime').html('');
	});
}

function checkSuspension() {
	if (IsUserAuthenticated === true) {
		IsMemberSuspendedForBooking().then(function (ret) {
			if (ret === true) {
				$('.suspended-booking').removeClass('hidden');
			}
		});
	}
}

//------- End of Common Methods ------------------------------------------