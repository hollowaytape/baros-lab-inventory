from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from inventory.models import Experiment, Material, Text, Room, Tag
from inventory.forms import ExperimentForm, RoomForm, MaterialForm
from django.forms.models import modelformset_factory

# Imports for add-or-edit object form.
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

def url_safe(string):
    """ Replaces spaces with underscores, making a string safer for urls."""
    return string.replace(' ', '_').replace("'", "").replace(".", "")

def eye_safe(string):
    """ Undoes the operation of url_safe()."""
    return string.replace('_', ' ')

def experiment_index(request):
    # Obtain the context from the HTTP request.
    context = RequestContext(request)
    
    # Query the database for a list of all experiments.
    # Order the experiments by session in ascending order.
    # Place the list in our context_dict dictionary,
    # which will be passed to the template engine.
    fr_experiments, jr_experiments, sr_experiments = [], [], []
    
    for e in Experiment.objects.filter(text__year="Freshman").order_by('session'):
        fr_experiments.append(e)
    
    for e in Experiment.objects.filter(text__year="Junior").order_by('session'):
        jr_experiments.append(e)
    
    for e in Experiment.objects.filter(text__year="Senior").order_by('session'):
        sr_experiments.append(e)
    
    context_dict = {}
    context_dict['fr_experiments'] = fr_experiments
    context_dict['jr_experiments'] = jr_experiments
    context_dict['sr_experiments'] = sr_experiments
    
    # Sanitize experiment names for use in urls.
    for year in (fr_experiments, jr_experiments, sr_experiments):
        for experiment in year:
            experiment.url = url_safe(experiment.title)
    
    # Render the response and send it back!
    return render_to_response('inventory/experiment_index.html', context_dict, context)

    
def experiment(request, experiment_name_url):
    context = RequestContext(request)
    
    # Change underscores in the experiment name to spaces.
    experiment_name = eye_safe(experiment_name_url)
    
    # Context dictionary to pass to the template.
    # Contain the name of the experiment passed by the user.
    context_dict = {'experiment_name': experiment_name}
    
    # Can we find an experiment with the given name?
    # If we can't, the .get() raises DoesNotExist.
    # SO the .get() method returns one model or raises an exception.
    experiment = get_object_or_404(Experiment, title=experiment_name)
    
    # Retrieve all of the experiment's materials and tags.
    materials = experiment.materials
    tags = experiment.tags
    
    # Create a list with the steps of the procedure separated.
    procedure = experiment.procedure.split('. ')
    
    # Add materials/procedure to the context dictionary.
    context_dict['materials'] = materials
    context_dict['tags'] = tags
    context_dict['procedure'] = procedure
    
    # Also add the experiment object.
    context_dict['experiment'] = experiment
    
    # Go render the response and return it to the client.
    return render_to_response('inventory/experiment.html', context_dict, context)

    
def tag(request, tag_name):
    context = RequestContext(request)
    
    # Context dictionary to pass to the template.
    # Contain the name of the room passed by the user.
    context_dict = {'tag_name': tag_name}
    
    # Can we find an experiment with the given name?
    # If we can't, the .get() raises DoesNotExist.
    # So the .get() method returns one model or raises an exception.
    tag = get_object_or_404(Tag, name = tag_name)
    
    # Retrieve all of the Experiment objects with this tag.
    # Maybe there is a more idiomatic way of doing this...
    experiments = []
    for e in Experiment.objects.all():
        if tag in e.tags.all():
            e.url = url_safe(e.title)
            experiments.append(e)
    
    # Add experiments to the context dictionary.
    context_dict['experiments'] = experiments
    
    # Also add the tag, so we can check if it exists.
    context_dict['tag'] = tag
    
    # Go render the response and return it to the client.
    return render_to_response('inventory/tag.html', context_dict, context)
    
def room_index(request):
    # Obtain the context from the HTTP request.
    context = RequestContext(request)
    
    # Query the database for a list of all rooms.
    # Order the rooms by number.
    # Place the list in our context_dict dictionary,
    # which will be passed to the template engine.
    room_list = Room.objects.order_by('number')
    context_dict = {'rooms': room_list}
    
    # Render the response and send it back!
    return render_to_response('inventory/room_index.html', context_dict, context)

def room(request, room_number):
    context = RequestContext(request)
    
    # Context dictionary to pass to the template.
    # Contain the name of the room passed by the user.
    context_dict = {'room_number': room_number}
    
    # Can we find an experiment with the given name?
    # If we can't, the .get() raises DoesNotExist.
    # SO the .get() method returns one model or raises an exception.
    room = get_object_or_404(Room, number=room_number)
    
    # Retrieve all of the materials in the room.
    materials = Material.objects.filter(room=room).order_by('location')
    
    # Add materials/procedure to the context dictionary.
    context_dict['materials'] = materials
    
    # Go render the response and return it to the client.
    return render_to_response('inventory/room.html', context_dict, context)
    
def rooms_all(request):
    # Obtain the context from the HTTP request.
    context = RequestContext(request)
    
    # Then, get each type of Material and add it to the dict.
    material_types = Material.objects.values('name').order_by().distinct()
    context_dict = {'materials': material_types}
    
    # Render the response and send it back!
    return render_to_response('inventory/rooms_all.html', context_dict, context)

def experiment_edit(request, id=None, template_name='inventory/experiment_edit.html'):
    if id:
        experiment = get_object_or_404(Experiment, pk=id)
    else:
        experiment = Experiment()
 
    if request.POST:
        form = ExperimentForm(request.POST, instance=experiment)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, _('Experiment correctly saved.'))
            # If the save was successful, redirect to another page
            redirect_url = reverse('experiment_index')
            return HttpResponseRedirect(redirect_url)
 
    else:
        form = ExperimentForm(instance=experiment)
 
    return render_to_response(template_name, {
        'form': form,
    }, context_instance=RequestContext(request))

def room_edit(request, number):
    room = Room.objects.get(number = number)
    MaterialFormSet = modelformset_factory(Material, form = MaterialForm)
    qset = Material.objects.filter(room = room)
    # Not sure why it is reassigned in this way - test as one assignment statement later?
    formset = MaterialFormSet(queryset = qset)
    if request.method == 'POST':
        # deal with posting the data
        formset = PointFormset(request.POST)
        if formset.is_valid():
            # if it is not valid then the "errors" will fall through and be returned
            formset.save()
        return HttpResponseRedirect(reverse('room_index'))

    context_dict = {'formset':formset,
                    'room':room,
                    }

    return render_to_response('inventory/room_edit.html', context_dict)
    
"""def room_edit(request, number=None): # Django snippets: "Form with one Formset example."
    if number == None:
        room = Room()
    else:
        room = Room.objects.get(number = number)
    
    MaterialFormSet = inlineformset_factory(Room, Material, queryset=Material.objects.filter(room=room), can_delete=True)
    
    if request.method == "POST":
        roomform = RoomForm(request.POST, instance=room)
        materialformset = MaterialFormSet(request.POST, request.FILES, instance=room)

        if roomform.is_valid() and materialformset.is_valid():
            roomform.save()
            materialformset.save()
            
            # Redirect somewhere
            if '_save' in request.POST:
                return HttpResponseRedirect(reverse('room_index'))
            if '_addanother' in request.POST:
                return HttpResponseRedirect(reverse('room_edit'))
                
    else:
        roomform = RoomForm(instance=room)
        materialformset = MaterialFormSet(instance=room)
        
    return render_to_response('inventory/room_edit.html', {
        'roomform' : roomform,
        'materialformset' : materialformset,
    })"""